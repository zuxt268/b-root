from abc import ABC, abstractmethod
import os
import re
import tempfile
import requests
from urllib.request import urlretrieve
from typing import Any, List, Optional
from domain.instagram_media import InstagramMedia
from domain.wordpress_source import WordPressSource
from service.slack_service import SlackService


class WordPressServiceBase(ABC):
    """Base class for WordPress services to eliminate duplication."""
    
    def __init__(self, wordpress_source: WordPressSource):
        self.wordpress_source = wordpress_source
        self._authenticate()
    
    @abstractmethod
    def _authenticate(self) -> None:
        """Perform authentication specific to the service type."""
        pass
    
    @abstractmethod
    def _get_auth_error_class(self) -> type:
        """Return the appropriate authentication error class."""
        pass
    
    @abstractmethod
    def _get_api_error_class(self) -> type:
        """Return the appropriate API error class."""
        pass
    
    def get_contents_html(self, instagram_media: InstagramMedia) -> str:
        """Generate HTML content from Instagram media caption."""
        if instagram_media.caption is None:
            return ""
        
        caption = instagram_media.caption
        caption = re.sub(r"#[^\s]+", "", caption)
        caption = re.sub(r"@[^\s]+", "", caption)
        caption = caption.strip()
        
        if not caption:
            return ""
            
        lines = caption.split('\n')
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        
        if not non_empty_lines:
            return ""
            
        paragraphs = []
        current_paragraph = []
        
        for line in non_empty_lines:
            if line == "":
                if current_paragraph:
                    paragraphs.append(" ".join(current_paragraph))
                    current_paragraph = []
            else:
                current_paragraph.append(line)
        
        if current_paragraph:
            paragraphs.append(" ".join(current_paragraph))
        
        html_paragraphs = [f"<p>{paragraph}</p>" for paragraph in paragraphs]
        return "".join(html_paragraphs)
    
    def get_html_for_image(self, url: str) -> str:
        """Generate HTML for single image."""
        return f"<div style='text-align: center;'><img src='{url}' style='margin: 0 auto;' width='500px' height='500px'/></div>"
    
    def get_html_for_carousel(self, urls: List[str]) -> str:
        """Generate HTML for image carousel."""
        images_html = ""
        for url in urls:
            images_html += self.get_html_for_image(url)
        return images_html
    
    def get_html_for_video(self, url: str) -> str:
        """Generate HTML for video."""
        return f"<div style='text-align: center;'><video controls width='500' height='500'><source src='{url}' type='video/mp4'>Your browser does not support the video tag.</video></div>"
    
    def get_title(self, instagram_media: InstagramMedia) -> str:
        """Extract title from Instagram media caption."""
        if instagram_media.caption is None:
            return "Untitled"
        
        caption = instagram_media.caption
        lines = caption.split('\n')
        
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#') and not line.startswith('@'):
                words = line.split()
                if len(words) >= 3:
                    return ' '.join(words[:10])
        
        return "Untitled"
    
    def posts(self, instagram_medias: List[InstagramMedia]) -> List[int]:
        """Main posting orchestration logic."""
        post_ids = []
        
        for instagram_media in instagram_medias:
            try:
                if instagram_media.media_type == "IMAGE":
                    post_id = self.post_for_image(instagram_media)
                elif instagram_media.media_type == "CAROUSEL_ALBUM":
                    post_id = self.post_for_carousel(instagram_media)
                elif instagram_media.media_type == "VIDEO":
                    post_id = self.post_for_video(instagram_media)
                else:
                    continue
                
                if post_id:
                    post_ids.append(post_id)
                    
            except Exception as e:
                SlackService().send_alert(f"Error posting media {instagram_media.id}: {str(e)}")
                continue
        
        return post_ids
    
    def transfer_image(self, media_url: str) -> Optional[str]:
        """Download and upload image to WordPress."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                urlretrieve(media_url, temp_file.name)
                
                with open(temp_file.name, 'rb') as file:
                    files = {'file': file}
                    response = requests.post(
                        f"{self.wordpress_source.url}/wp-json/wp/v2/media",
                        files=files,
                        headers=self._get_auth_headers()
                    )
                
                os.unlink(temp_file.name)
                
                if response.status_code == 201:
                    return response.json().get('source_url')
                    
        except Exception as e:
            SlackService().send_alert(f"Error transferring image: {str(e)}")
            
        return None
    
    def transfer_video(self, media_url: str) -> Optional[str]:
        """Download and upload video to WordPress."""
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
                urlretrieve(media_url, temp_file.name)
                
                with open(temp_file.name, 'rb') as file:
                    files = {'file': file}
                    response = requests.post(
                        f"{self.wordpress_source.url}/wp-json/wp/v2/media",
                        files=files,
                        headers=self._get_auth_headers()
                    )
                
                os.unlink(temp_file.name)
                
                if response.status_code == 201:
                    return response.json().get('source_url')
                    
        except Exception as e:
            SlackService().send_alert(f"Error transferring video: {str(e)}")
            
        return None
    
    @abstractmethod
    def _get_auth_headers(self) -> dict:
        """Get authentication headers for WordPress API."""
        pass
    
    def post_for_image(self, instagram_media: InstagramMedia) -> Optional[int]:
        """Post single image to WordPress."""
        uploaded_url = self.transfer_image(instagram_media.media_url)
        if not uploaded_url:
            return None
            
        return self._create_post(instagram_media, self.get_html_for_image(uploaded_url))
    
    def post_for_carousel(self, instagram_media: InstagramMedia) -> Optional[int]:
        """Post carousel to WordPress."""
        uploaded_urls = []
        
        for child in instagram_media.children:
            if child.media_type == "IMAGE":
                uploaded_url = self.transfer_image(child.media_url)
                if uploaded_url:
                    uploaded_urls.append(uploaded_url)
        
        if not uploaded_urls:
            return None
            
        return self._create_post(instagram_media, self.get_html_for_carousel(uploaded_urls))
    
    def post_for_video(self, instagram_media: InstagramMedia) -> Optional[int]:
        """Post video to WordPress."""
        uploaded_url = self.transfer_video(instagram_media.media_url)
        if not uploaded_url:
            return None
            
        return self._create_post(instagram_media, self.get_html_for_video(uploaded_url))
    
    def _create_post(self, instagram_media: InstagramMedia, content_html: str) -> Optional[int]:
        """Create WordPress post."""
        try:
            post_data = {
                'title': self.get_title(instagram_media),
                'content': content_html + self.get_contents_html(instagram_media),
                'status': 'publish'
            }
            
            response = requests.post(
                f"{self.wordpress_source.url}/wp-json/wp/v2/posts",
                json=post_data,
                headers=self._get_auth_headers()
            )
            
            if response.status_code == 201:
                return response.json().get('id')
                
        except Exception as e:
            SlackService().send_alert(f"Error creating post: {str(e)}")
            
        return None