
DROP TABLE IF EXISTS `admin_users`;

CREATE TABLE `admin_users` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


LOCK TABLES `admin_users` WRITE;
INSERT INTO `admin_users` VALUES (1,'yuki-ikezawa','y.ikezawa93@gmail.com','scrypt:32768:8:1$dRREkHP0QyGjLiPV$53799b2522f0097c6d4b3a7b0cff6218c5e04cc5702ef1b4fa17fad616bb62451bf13e608d3534709995377122b2ade58a2b4980d18ec9e8e5078819f37b5749'),(4,'池澤勇輝','y.ikezawa93+10@gmail.com','scrypt:32768:8:1$ox7bhiIFmCWoADNU$6bd5b4731ff9cabb3d9946294ae71138f23d6b30aec78af1234f00d3b348864547376b0d0f0a4b32287c375284e61bc4eb2f2560f947e1c4d86c91ce794341f4'),(6,'池澤勇輝2','y.ikezawa93+11@gmail.com','scrypt:32768:8:1$SrOkHalUVASATMYD$e6d8cbfd277ba47cf65bb48d373bba4f69381d205aec62ad2b516ac746522a47b08a0ddaa03bcfc74203194c3639c09b78c3f2d46d88a0740b410326e337e5ba');
UNLOCK TABLES;

DROP TABLE IF EXISTS `posts`;

CREATE TABLE `posts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `media_id` varchar(45) NOT NULL,
  `customer_id` int NOT NULL,
  `timestamp` varchar(45) NOT NULL,
  `media_url` mediumtext NOT NULL,
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `permalink` varchar(255) NOT NULL,
  `wordpress_link` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=53 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


DROP TABLE IF EXISTS `customers`;

CREATE TABLE `customers` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(255) NOT NULL,
  `email` varchar(255) NOT NULL,
  `password` varchar(255) NOT NULL,
  `wordpress_url` varchar(255) NOT NULL,
  `facebook_token` varchar(255) DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email_UNIQUE` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
