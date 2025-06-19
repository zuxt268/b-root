<?php
/*
  Plugin Name: A-Rootアダプター
  Description: A-Rootと連携して、APIキーによる認証を通じたWordPress記事の自動投稿およびメディアファイルのアップロードを実現します。
  Version: 1.0.1
  Author: IkezawaYuki
*/

require_once(ABSPATH . 'wp-admin/includes/file.php');
require_once(ABSPATH . 'wp-admin/includes/image.php');
require_once(ABSPATH . 'wp-admin/includes/media.php');


function verify_api_token($api_key): bool
{
    $hash_data = get_option('a_root_api_key');
    if (empty($hash_data)) {
        return false;
    }
    $api_key_hash = hash('sha256', $api_key);
    return hash_equals($hash_data, $api_key_hash);
}

function get_version(WP_REST_Request $request): WP_REST_Response
{
    return new WP_REST_Response(array(
        'version' => "v1.0.1"), 200);
}

function get_client_ip(WP_REST_Request $request) {
    // クライアントのIPアドレスを取得
    if (!empty($_SERVER['HTTP_CLIENT_IP'])) {
        // プロキシ経由のIPアドレス
        $ip = $_SERVER['HTTP_CLIENT_IP'];
    } elseif (!empty($_SERVER['HTTP_X_FORWARDED_FOR'])) {
        // フォワーディングされたIPアドレス
        $ip = explode(',', $_SERVER['HTTP_X_FORWARDED_FOR'])[0];
    } else {
        // リモートアドレス
        $ip = $_SERVER['REMOTE_ADDR'];
    }
    return $ip;
}

// POSTリクエストに対応するコールバック関数（記事投稿）
function create_post(WP_REST_Request $request) {

    if (get_client_ip($request) !== "162.43.19.187") {
        return new WP_REST_Response(array(
            'error' => 'Access denied',
        ), 400);
    }

    $params = $request->get_json_params();

    // JWTの取得と検証
    $api_key = $params['api_key'] ?? '';
    if (!verify_api_token($api_key)) {
        return new WP_REST_Response(array('error' => 'Invalid api key'), 401);
    }

    $admins = get_users(array(
        'role'    => 'administrator',
        'number'  => 1, // 最初の1件のみ取得
        'orderby' => 'ID',
        'order'   => 'ASC'
    ));
    if (empty($admins)) {
        return new WP_REST_Response(array('error' => 'No administrator found'), 404);
    }
    $user = $admins[0];

    // 記事のデータを取得
    $title = sanitize_text_field($params['title'] ?? '');
    $content = $params['content'];
    $media_id = isset($params['featured_media']) ? intval($params['featured_media']) : 0;

    if (empty($content)) {
        return new WP_REST_Response(array('error' => 'Content are required'), 400);
    }

    // 記事を投稿する
    $post_id = wp_insert_post(array(
        'post_title'   => $title,
        'post_content' => $content,
        'post_status'  => 'publish',
        'post_author'  => $user->ID, // 投稿者ID。
    ));

    if (!empty($media_id)) {
        set_post_thumbnail($post_id, $media_id);
    }

    // 記事のURLを取得
    $post_url = get_permalink($post_id);

    if (is_wp_error($post_id)) {
        return new WP_REST_Response(array('error' => 'Failed to create post'), 500);
    }

    return new WP_REST_Response(array(
        'message' => 'Post created successfully',
        'post_id' => $post_id,
        'post_url' => $post_url), 200);
}
function upload_media(WP_REST_Request $request)
{
    if (get_client_ip($request) !== "162.43.19.187") {
        return new WP_REST_Response(array(
            'error' => 'Access denied',
        ), 400);
    }

    $api_key = sanitize_text_field($_POST['api_key'] ?? '');

    if (!verify_api_token($api_key)) {
        return new WP_REST_Response(array('error' => 'Invalid api key'), 401);
    }

    if (!isset($_FILES['file'])) {
        return new WP_REST_Response(['error' => 'No file uploaded'], 400);
    }

    // ファイル情報の取得とアップロード処理
    $file = $_FILES['file'];

    if ($_FILES['file']['size'] > 1073741824) { // 1GBのファイルサイズ制限
        return new WP_REST_Response(['error' => 'File size exceeds limit'], 400);
    }

    $allowed_types = ['image/jpeg', 'image/png', 'video/mp4'];
    if (!in_array($file['type'], $allowed_types)) {
        return new WP_REST_Response(['error' => 'Unsupported file type'], 400);
    }

    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime_type = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mime_type, $allowed_types)) {
        return new WP_REST_Response(['error' => 'Unsupported file type'], 400);
    }

    $uploaded_file = wp_handle_upload($file, ['test_form' => false]);
    if (isset($uploaded_file['error'])) {
        return new WP_REST_Response(['error' => $uploaded_file['error']], 500);
    }

    $filename = $uploaded_file['file'];
    $filetype = wp_check_filetype($filename, null);

    $attachment = array(
        'post_mime_type' => $filetype['type'],
        'post_title'     => sanitize_file_name(basename($filename)),
        'post_content'   => '',
        'post_status'    => 'inherit'
    );

    // メディアライブラリに添付ファイルとして登録
    $attach_id = wp_insert_attachment($attachment, $filename);

    // 添付ファイルのメタデータを生成して保存
    $attach_data = wp_generate_attachment_metadata($attach_id, $filename);
    wp_update_attachment_metadata($attach_id, $attach_data);

    // アップロード結果をレスポンスとして返す
    return new WP_REST_Response([
        'id' => $attach_id,
        'source_url' => wp_get_attachment_url($attach_id),
        'mime_type' => $mime_type,
    ], 201);
}

function rodut_enqueue_single_post_styles(): void
{
    // シングル投稿ページの場合にのみスタイルを読み込む
    wp_enqueue_style(
        'rodut-single-post-style', // スタイルのハンドル名
        plugin_dir_url(__FILE__) . 'a-root.css', // CSSファイルへのパス
        array(), // 依存関係のスタイル（ない場合は空配列）
        '1.0.0' // バージョン番号
    );
}

function rodut_enqueue_slick_carousel(): void
{
    if (is_singular('post')) {
        // SlickのCSSを読み込む
        wp_enqueue_style('slick-css', 'https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.css', array(), '1.9.0');
        wp_enqueue_style('slick-theme-css', 'https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick-theme.css', array(), '1.9.0');

        // SlickのJavaScriptを読み込む
        wp_enqueue_script('slick-js', 'https://cdnjs.cloudflare.com/ajax/libs/slick-carousel/1.9.0/slick.min.js', array('jquery'), '1.9.0', true);

        // カスタムJavaScriptをインラインで追加（Slickの初期化処理）
        wp_add_inline_script('slick-js', "
        jQuery(document).ready(function(){
            jQuery('.a-root-wordpress-instagram-slider').slick({
                dots: true
            });
        });
    ");
    }
}

function get_title(WP_REST_Request $request): WP_REST_Response {
    $site_title = get_bloginfo('name');
    $ary = [
        "title" => $site_title,
    ];
    return new WP_REST_Response($ary, 200);
}

// REST APIエンドポイントを登録するフック
add_action('rest_api_init', function() {
    register_rest_route('rodut/v1', '/version', array(
        'methods' => 'GET',
        'callback' => 'get_version',
    ));

    // 記事投稿のエンドポイント
    register_rest_route('rodut/v1', '/create-post', array(
        'methods' => 'POST',
        'callback' => 'create_post',
    ));

    // メディアアップロードのエンドポイント
    register_rest_route('rodut/v1', '/upload-media', array(
        'methods' => 'POST',
        'callback' => 'upload_media',
    ));

    // サイトのタイトル取得、A-Rootにて使用する
    register_rest_route('rodut/v1', '/title', array(
        'methods' => 'GET',
        'callback' => 'get_title',
    ));
});

add_action('wp_enqueue_scripts', 'rodut_enqueue_slick_carousel');
add_action('wp_enqueue_scripts', 'rodut_enqueue_single_post_styles');

// 管理画面の設定メニュー
add_action('admin_menu', function () {
    add_menu_page(
        'A-Root', // ページタイトル
        'A-Root', // メニューに表示されるテキスト
        'manage_options', // 権限
        'a_root_setting', // スラッグ
        'a_root_setting_page', // コールバック関数
        'dashicons-instagram'
    );
});

// 設定ページのUI
function a_root_setting_page(): void
{
    ?>
    <div class="wrap">
        <h1>A-Root設定</h1>
        <form method="post" action="options.php">
            <?php
            settings_fields('a_root_group');
            do_settings_sections('a_root_settings');
            submit_button();
            ?>
        </form>
    </div>
    <?php
}

// 設定項目の登録
add_action('admin_init', function() {
    register_setting('a_root_group', 'a_root_api_key');

    add_settings_section('a_root_section', 'A-Root APIキー', null, 'a_root_settings');

    add_settings_field('a_root_api_key', 'A-Root APIキー', function() {
        $val = esc_attr(get_option('a_root_api_key', ''));
        ?>
        <style>
            .api-key-wrapper {
                position: relative;
                display: inline-block;
            }
            .api-key-toggle {
                position: absolute;
                top: 50%;
                right: 10px;
                transform: translateY(-50%);
                cursor: pointer;
                font-size: 16px;
                color: #666;
            }
        </style>

        <div class="api-key-wrapper">
            <input type="password" name="a_root_api_key" id="a_root_api_key" value="<?php echo $val; ?>" size="60" />
            <span class="api-key-toggle dashicons dashicons-visibility" id="toggle_api_key_visibility" title="表示/非表示切替"></span>
        </div>

        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const toggle = document.getElementById('toggle_api_key_visibility');
                const input = document.getElementById('a_root_api_key');

                toggle.addEventListener('click', function () {
                    const isPassword = input.type === 'password';
                    input.type = isPassword ? 'text' : 'password';
                    toggle.className = isPassword
                        ? 'api-key-toggle dashicons dashicons-hidden'
                        : 'api-key-toggle dashicons dashicons-visibility';
                });
            });
        </script>
        <?php
    }, 'a_root_settings', 'a_root_section');
});

add_filter('plugin_action_links_' . plugin_basename(__FILE__), 'a_root_add_settings_link');

function a_root_add_settings_link($links) {
    $settings_link = '<a href="' . admin_url('admin.php?page=a_root_setting') . '">設定</a>';
    array_unshift($links, $settings_link); // 最初に表示
    return $links;
}