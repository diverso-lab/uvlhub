/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19-11.8.3-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: db    Database: uvlhubdb
-- ------------------------------------------------------
-- Server version	12.0.2-MariaDB-ubu2404

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*M!100616 SET @OLD_NOTE_VERBOSITY=@@NOTE_VERBOSITY, NOTE_VERBOSITY=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `alembic_version` VALUES
('8a96e53e7e32');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `api_keys`
--

DROP TABLE IF EXISTS `api_keys`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_keys` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key` varchar(64) NOT NULL,
  `user_id` int(11) NOT NULL,
  `scopes` varchar(256) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `last_used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `key` (`key`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `api_keys_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `api_keys`
--

LOCK TABLES `api_keys` WRITE;
/*!40000 ALTER TABLE `api_keys` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `api_keys` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `author`
--

DROP TABLE IF EXISTS `author`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `author` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `affiliation` varchar(120) DEFAULT NULL,
  `orcid` varchar(19) DEFAULT NULL,
  `ds_meta_data_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_meta_data_id` (`ds_meta_data_id`),
  CONSTRAINT `author_ibfk_1` FOREIGN KEY (`ds_meta_data_id`) REFERENCES `ds_meta_data` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `author`
--

LOCK TABLES `author` WRITE;
/*!40000 ALTER TABLE `author` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `author` VALUES
(4,'Author 4','Affiliation 4','0000-0000-0000-0003',4),
(5,'John Doe','Some University','',5);
/*!40000 ALTER TABLE `author` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `datasets`
--

DROP TABLE IF EXISTS `datasets`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `datasets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `ds_meta_data_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `feature_model_count` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_meta_data_id` (`ds_meta_data_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `datasets_ibfk_1` FOREIGN KEY (`ds_meta_data_id`) REFERENCES `ds_meta_data` (`id`),
  CONSTRAINT `datasets_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `datasets`
--

LOCK TABLES `datasets` WRITE;
/*!40000 ALTER TABLE `datasets` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `datasets` VALUES
(4,2,4,'2025-12-16 11:23:56',3),
(5,1,5,'2025-12-16 11:31:17',0);
/*!40000 ALTER TABLE `datasets` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `doi_mapping`
--

DROP TABLE IF EXISTS `doi_mapping`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `doi_mapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_doi_old` varchar(120) DEFAULT NULL,
  `dataset_doi_new` varchar(120) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `doi_mapping`
--

LOCK TABLES `doi_mapping` WRITE;
/*!40000 ALTER TABLE `doi_mapping` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `doi_mapping` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `ds_download_record`
--

DROP TABLE IF EXISTS `ds_download_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ds_download_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `dataset_id` int(11) DEFAULT NULL,
  `download_date` datetime NOT NULL,
  `download_cookie` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_id` (`dataset_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `ds_download_record_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`),
  CONSTRAINT `ds_download_record_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ds_download_record`
--

LOCK TABLES `ds_download_record` WRITE;
/*!40000 ALTER TABLE `ds_download_record` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `ds_download_record` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `ds_meta_data`
--

DROP TABLE IF EXISTS `ds_meta_data`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ds_meta_data` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `deposition_id` int(11) DEFAULT NULL,
  `title` varchar(120) NOT NULL,
  `description` text NOT NULL,
  `publication_type` enum('ANNOTATION_COLLECTION','BOOK','BOOK_SECTION','CONFERENCE_PAPER','DATA_MANAGEMENT_PLAN','JOURNAL_ARTICLE','PATENT','PREPRINT','PROJECT_DELIVERABLE','PROJECT_MILESTONE','PROPOSAL','REPORT','SOFTWARE_DOCUMENTATION','TAXONOMIC_TREATMENT','TECHNICAL_NOTE','THESIS','WORKING_PAPER','OTHER') DEFAULT NULL,
  `publication_doi` varchar(120) DEFAULT NULL,
  `dataset_doi` varchar(120) DEFAULT NULL,
  `tags` varchar(120) DEFAULT NULL,
  `ds_metrics_id` int(11) DEFAULT NULL,
  `dataset_anonymous` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_metrics_id` (`ds_metrics_id`),
  CONSTRAINT `ds_meta_data_ibfk_1` FOREIGN KEY (`ds_metrics_id`) REFERENCES `ds_metrics` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=6 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ds_meta_data`
--

LOCK TABLES `ds_meta_data` WRITE;
/*!40000 ALTER TABLE `ds_meta_data` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `ds_meta_data` VALUES
(4,4,'Sample dataset 4','Description for dataset 4','DATA_MANAGEMENT_PLAN','https://www.doi.org/10.1234/dataset4','10.1234/dataset4','tag1, tag2',NULL,0),
(5,NULL,'sfgdsdgfsg','<p>sdfgsdgf</p>',NULL,'',NULL,'',NULL,0);
/*!40000 ALTER TABLE `ds_meta_data` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `ds_metrics`
--

DROP TABLE IF EXISTS `ds_metrics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ds_metrics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `number_of_models` int(11) DEFAULT NULL,
  `number_of_features` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ds_metrics`
--

LOCK TABLES `ds_metrics` WRITE;
/*!40000 ALTER TABLE `ds_metrics` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `ds_metrics` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `ds_view_record`
--

DROP TABLE IF EXISTS `ds_view_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ds_view_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `dataset_id` int(11) NOT NULL,
  `view_date` datetime NOT NULL,
  `view_cookie` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_id` (`dataset_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `ds_view_record_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`),
  CONSTRAINT `ds_view_record_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ds_view_record`
--

LOCK TABLES `ds_view_record` WRITE;
/*!40000 ALTER TABLE `ds_view_record` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `ds_view_record` VALUES
(3,1,4,'2025-12-16 12:03:44','a8e11633-67d3-4a74-92bd-56ac638c6580');
/*!40000 ALTER TABLE `ds_view_record` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `elasticsearch`
--

DROP TABLE IF EXISTS `elasticsearch`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `elasticsearch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `elasticsearch`
--

LOCK TABLES `elasticsearch` WRITE;
/*!40000 ALTER TABLE `elasticsearch` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `elasticsearch` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `feature_model`
--

DROP TABLE IF EXISTS `feature_model`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `feature_model` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_feature_model_dataset_id` (`dataset_id`),
  CONSTRAINT `feature_model_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `feature_model`
--

LOCK TABLES `feature_model` WRITE;
/*!40000 ALTER TABLE `feature_model` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `feature_model` VALUES
(10,4),
(11,4),
(12,4),
(13,5);
/*!40000 ALTER TABLE `feature_model` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `flamapy`
--

DROP TABLE IF EXISTS `flamapy`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `flamapy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flamapy`
--

LOCK TABLES `flamapy` WRITE;
/*!40000 ALTER TABLE `flamapy` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `flamapy` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `hubfile_download_record`
--

DROP TABLE IF EXISTS `hubfile_download_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hubfile_download_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `file_id` int(11) NOT NULL,
  `download_date` datetime NOT NULL,
  `download_cookie` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `file_id` (`file_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `hubfile_download_record_ibfk_1` FOREIGN KEY (`file_id`) REFERENCES `hubfiles` (`id`),
  CONSTRAINT `hubfile_download_record_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hubfile_download_record`
--

LOCK TABLES `hubfile_download_record` WRITE;
/*!40000 ALTER TABLE `hubfile_download_record` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `hubfile_download_record` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `hubfile_view_record`
--

DROP TABLE IF EXISTS `hubfile_view_record`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hubfile_view_record` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) DEFAULT NULL,
  `file_id` int(11) NOT NULL,
  `view_date` datetime DEFAULT NULL,
  `view_cookie` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `file_id` (`file_id`),
  KEY `user_id` (`user_id`),
  CONSTRAINT `hubfile_view_record_ibfk_1` FOREIGN KEY (`file_id`) REFERENCES `hubfiles` (`id`),
  CONSTRAINT `hubfile_view_record_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hubfile_view_record`
--

LOCK TABLES `hubfile_view_record` WRITE;
/*!40000 ALTER TABLE `hubfile_view_record` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `hubfile_view_record` VALUES
(2,1,10,'2025-12-16 12:04:16','a8e11633-67d3-4a74-92bd-56ac638c6580');
/*!40000 ALTER TABLE `hubfile_view_record` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `hubfiles`
--

DROP TABLE IF EXISTS `hubfiles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `hubfiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `checksum` varchar(120) NOT NULL,
  `size` int(11) NOT NULL,
  `feature_model_id` int(11) NOT NULL,
  `factlabel_json` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `feature_model_id` (`feature_model_id`),
  CONSTRAINT `hubfiles_ibfk_1` FOREIGN KEY (`feature_model_id`) REFERENCES `feature_model` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `hubfiles`
--

LOCK TABLES `hubfiles` WRITE;
/*!40000 ALTER TABLE `hubfiles` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `hubfiles` VALUES
(10,'file10.uvl','checksum10',414,10,'{\"metadata\": [{\"name\": \"Name\", \"description\": \"Name of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"file10.uvl\", \"size\": null, \"ratio\": null}, {\"name\": \"Description\", \"description\": \"Description of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Description for dataset 4\", \"size\": null, \"ratio\": null}, {\"name\": \"Author\", \"description\": \"Author of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Year\", \"description\": \"Year of creation of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Reference\", \"description\": \"Main paper for reference or DOI of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Tags\", \"description\": \"Tags or keywords that identify the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"tag1\", \" tag2\"], \"size\": null, \"ratio\": null}, {\"name\": \"Domain\", \"description\": \"Domain of the feature model.\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Language level\", \"description\": \"Language level of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Boolean\", \"size\": null, \"ratio\": null}], \"metrics\": [{\"name\": \"Features\", \"description\": \"Set of features in the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": null}, {\"name\": \"Abstract features\", \"description\": \"Features used to structure the feature model that, however, do not have any impact at implementation level.\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract leaf features\", \"description\": \"Abstract and leaf features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract compound features\", \"description\": \"Abstract and compound features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Concrete features\", \"description\": \"Features that are mapped to at least one implementation artifact.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": 1.0}, {\"name\": \"Concrete leaf features\", \"description\": \"Concrete and leaf features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Concrete compound features\", \"description\": \"Concrete and compound features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Compound features\", \"description\": \"Features that have subfeatures.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Leaf features\", \"description\": \"Features that have not subfeatures (aka \'primitive features\' or \'terminal features\').\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Root feature\", \"description\": \"The root of the feature model.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\"], \"size\": 1, \"ratio\": 0.1}, {\"name\": \"Top features\", \"description\": \"Features that are first descendants of the root.\", \"parent\": \"Root feature\", \"level\": 2, \"value\": [\"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 4, \"ratio\": 0.4}, {\"name\": \"Solitary features\", \"description\": \"Features that are not grouped in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Grouped features\", \"description\": \"Features that occurs in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Typed features\", \"description\": \"Non-Boolean features its selection require to provide a value (e.g., a number, a string,...\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Numerical features\", \"description\": \"Features with a Integer or Real type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Integer features\", \"description\": \"Features with a Integer type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Real features\", \"description\": \"Features with a Real type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"String features\", \"description\": \"Features with a String type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Multi-features\", \"description\": \"Features with cardinalities (aka \'clonable features\')\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Tree relationships\", \"description\": \"Number of relationships (edges) of the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"(mandatory) Chat[1,1]Connection\", \"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(mandatory) Chat[1,1]Messages\", \"(or) Messages[1,3]Text Video Audio\", \"(optional) Chat[0,1]Data Storage\", \"(optional) Chat[0,1]Media Player\"], \"size\": 6, \"ratio\": null}, {\"name\": \"Mandatory features\", \"description\": \"Features marked as mandatory that need to be selected if its parent is selected.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Optional features\", \"description\": \"Feature marked as optional.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Feature groups\", \"description\": \"Features that express a choice over the grouped features in a group.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(or) Messages[1,3]Text Video Audio\"], \"size\": 2, \"ratio\": 0.33}, {\"name\": \"Alternative groups\", \"description\": \"Feature groups that require the selection of just one child (i.e., [1..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Or groups\", \"description\": \"Feature groups that require the selection of at least one child (i.e., [1..*] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(or) Messages[1,3]Text Video Audio\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Mutex groups\", \"description\": \"Feature groups that require the selection of zero or just one child (i.e., [0..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Cardinality groups\", \"description\": \"Feature groups with arbitraty cardinality [a..b] that require the selection of an minimum and a maximum number of children.\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Depth of tree\", \"description\": \"Number of features of the longest path from the root to the leaf features.\", \"parent\": null, \"level\": 0, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Mean depth of tree\", \"description\": \"Number of features of the mean path from the root to the leaf features.\", \"parent\": \"Depth of tree\", \"level\": 1, \"value\": 1.71, \"size\": null, \"ratio\": null}, {\"name\": \"Branching factor\", \"description\": \"Average number of children per non-leaf feature (aka \'Ratio of Variability\').\", \"parent\": null, \"level\": 0, \"value\": 3.0, \"size\": null, \"ratio\": null}, {\"name\": \"Min children per feature\", \"description\": \"Minimal number of children per non-leaf feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max children per feature\", \"description\": \"Maximal number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 4, \"size\": null, \"ratio\": null}, {\"name\": \"Avg children per feature\", \"description\": \"Average number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 0.9, \"size\": null, \"ratio\": null}, {\"name\": \"Cross-tree constraints\", \"description\": \"Textual cross-tree constraints.\", \"parent\": null, \"level\": 0, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": null}, {\"name\": \"Logical constraints\", \"description\": \"Constraints with only logical operators.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": 1.0}, {\"name\": \"Single feature constraints\", \"description\": \"Constraints with a single feature or negated feature.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Simple constraints\", \"description\": \"Requires and Excludes constraints.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Requires constraints\", \"description\": \"Constraints modeling that the activation of a feature f1 implies the activation of a feature f2.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Excludes constraints\", \"description\": \"Constraints modeling that two features are mutually exclusive and cannot be activated together.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Complex constraints\", \"description\": \"Constraints in arbitrary propositional logic formulae.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Pseudo-complex constraints\", \"description\": \"Constraints that are convertible to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Strict-complex constraints\", \"description\": \"Constraints that cannot be converted to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Arithmetic constraints\", \"description\": \"Constraints with at least one arithmetic operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Aggregation constraints\", \"description\": \"Constraints with at least one aggregation operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Features in constraints\", \"description\": \"Features involved in cross-tree constraints. The ratio to the total number of features is called \'Extra constraint representativeness (ECR)\'.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Video\", \"Data Storage\", \"Audio\", \"Media Player\", \"Server\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Min features per constraint\", \"description\": \"The minimal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max features per constraint\", \"description\": \"The maximal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 3, \"size\": null, \"ratio\": null}, {\"name\": \"Avg features per constraint\", \"description\": \"The average number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2.5, \"size\": null, \"ratio\": null}, {\"name\": \"Avg constraints per feature\", \"description\": \"The average number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Min constraints per feature\", \"description\": \"The minimal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Max constraints per feature\", \"description\": \"The maximal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Attributes\", \"description\": \"Features attributes in the model (i.e., number of distinct attributes).\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": null}, {\"name\": \"Features with attributes\", \"description\": \"Features that contain some attributes defined in the model.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Min attributes per feature\", \"description\": \"The minimal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Max attributes per feature\", \"description\": \"The maximal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature\", \"description\": \"Average number of attributes in features.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature w. attributes\", \"description\": \"Average number of attributes in features with attributes.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}], \"analysis\": [{\"name\": \"Satisfiable (valid)\", \"description\": \"A feature model is satisfiable (valid, not void) if it represents at least one configuration.\", \"parent\": null, \"level\": 0, \"value\": \"Yes\", \"size\": null, \"ratio\": null}, {\"name\": \"Core features\", \"description\": \"Features that are part of all the configurations (aka \'common features\').\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"False-optional features\", \"description\": \"Features included in all possible configurations although not being modelled as mandatory. The ratio is based on the total number of features.\", \"parent\": \"Core features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Dead features\", \"description\": \"Features that cannot appear in any configuration.\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Variant features\", \"description\": \"Features that appear only in some configurations (i.e., features that are neither core nor dead).\", \"parent\": null, \"level\": 0, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Configurations\", \"description\": \"Number of configurations represented by the feature model. If <= is shown, the number represents an upper estimation bound.\", \"parent\": null, \"level\": 0, \"value\": \"\\u2264 56\", \"size\": null, \"ratio\": null}, {\"name\": \"Total variability\", \"description\": \"The total variability measures the flexibility of the SPL considering all features.\", \"parent\": null, \"level\": 0, \"value\": \"5.47%\", \"size\": null, \"ratio\": null}, {\"name\": \"Partial variability\", \"description\": \"The partial variability measures the flexibility of the SPL considering only variant features.\", \"parent\": null, \"level\": 0, \"value\": \"44.09%\", \"size\": null, \"ratio\": null}]}'),
(11,'file11.uvl','checksum11',414,11,'{\"metadata\": [{\"name\": \"Name\", \"description\": \"Name of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"file11.uvl\", \"size\": null, \"ratio\": null}, {\"name\": \"Description\", \"description\": \"Description of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Description for dataset 4\", \"size\": null, \"ratio\": null}, {\"name\": \"Author\", \"description\": \"Author of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Year\", \"description\": \"Year of creation of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Reference\", \"description\": \"Main paper for reference or DOI of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Tags\", \"description\": \"Tags or keywords that identify the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"tag1\", \" tag2\"], \"size\": null, \"ratio\": null}, {\"name\": \"Domain\", \"description\": \"Domain of the feature model.\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Language level\", \"description\": \"Language level of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Boolean\", \"size\": null, \"ratio\": null}], \"metrics\": [{\"name\": \"Features\", \"description\": \"Set of features in the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": null}, {\"name\": \"Abstract features\", \"description\": \"Features used to structure the feature model that, however, do not have any impact at implementation level.\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract leaf features\", \"description\": \"Abstract and leaf features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract compound features\", \"description\": \"Abstract and compound features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Concrete features\", \"description\": \"Features that are mapped to at least one implementation artifact.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": 1.0}, {\"name\": \"Concrete leaf features\", \"description\": \"Concrete and leaf features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Concrete compound features\", \"description\": \"Concrete and compound features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Compound features\", \"description\": \"Features that have subfeatures.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Leaf features\", \"description\": \"Features that have not subfeatures (aka \'primitive features\' or \'terminal features\').\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Root feature\", \"description\": \"The root of the feature model.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\"], \"size\": 1, \"ratio\": 0.1}, {\"name\": \"Top features\", \"description\": \"Features that are first descendants of the root.\", \"parent\": \"Root feature\", \"level\": 2, \"value\": [\"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 4, \"ratio\": 0.4}, {\"name\": \"Solitary features\", \"description\": \"Features that are not grouped in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Grouped features\", \"description\": \"Features that occurs in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Typed features\", \"description\": \"Non-Boolean features its selection require to provide a value (e.g., a number, a string,...\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Numerical features\", \"description\": \"Features with a Integer or Real type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Integer features\", \"description\": \"Features with a Integer type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Real features\", \"description\": \"Features with a Real type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"String features\", \"description\": \"Features with a String type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Multi-features\", \"description\": \"Features with cardinalities (aka \'clonable features\')\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Tree relationships\", \"description\": \"Number of relationships (edges) of the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"(mandatory) Chat[1,1]Connection\", \"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(mandatory) Chat[1,1]Messages\", \"(or) Messages[1,3]Text Video Audio\", \"(optional) Chat[0,1]Data Storage\", \"(optional) Chat[0,1]Media Player\"], \"size\": 6, \"ratio\": null}, {\"name\": \"Mandatory features\", \"description\": \"Features marked as mandatory that need to be selected if its parent is selected.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Optional features\", \"description\": \"Feature marked as optional.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Feature groups\", \"description\": \"Features that express a choice over the grouped features in a group.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(or) Messages[1,3]Text Video Audio\"], \"size\": 2, \"ratio\": 0.33}, {\"name\": \"Alternative groups\", \"description\": \"Feature groups that require the selection of just one child (i.e., [1..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Or groups\", \"description\": \"Feature groups that require the selection of at least one child (i.e., [1..*] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(or) Messages[1,3]Text Video Audio\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Mutex groups\", \"description\": \"Feature groups that require the selection of zero or just one child (i.e., [0..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Cardinality groups\", \"description\": \"Feature groups with arbitraty cardinality [a..b] that require the selection of an minimum and a maximum number of children.\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Depth of tree\", \"description\": \"Number of features of the longest path from the root to the leaf features.\", \"parent\": null, \"level\": 0, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Mean depth of tree\", \"description\": \"Number of features of the mean path from the root to the leaf features.\", \"parent\": \"Depth of tree\", \"level\": 1, \"value\": 1.71, \"size\": null, \"ratio\": null}, {\"name\": \"Branching factor\", \"description\": \"Average number of children per non-leaf feature (aka \'Ratio of Variability\').\", \"parent\": null, \"level\": 0, \"value\": 3.0, \"size\": null, \"ratio\": null}, {\"name\": \"Min children per feature\", \"description\": \"Minimal number of children per non-leaf feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max children per feature\", \"description\": \"Maximal number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 4, \"size\": null, \"ratio\": null}, {\"name\": \"Avg children per feature\", \"description\": \"Average number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 0.9, \"size\": null, \"ratio\": null}, {\"name\": \"Cross-tree constraints\", \"description\": \"Textual cross-tree constraints.\", \"parent\": null, \"level\": 0, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": null}, {\"name\": \"Logical constraints\", \"description\": \"Constraints with only logical operators.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": 1.0}, {\"name\": \"Single feature constraints\", \"description\": \"Constraints with a single feature or negated feature.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Simple constraints\", \"description\": \"Requires and Excludes constraints.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Requires constraints\", \"description\": \"Constraints modeling that the activation of a feature f1 implies the activation of a feature f2.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Excludes constraints\", \"description\": \"Constraints modeling that two features are mutually exclusive and cannot be activated together.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Complex constraints\", \"description\": \"Constraints in arbitrary propositional logic formulae.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Pseudo-complex constraints\", \"description\": \"Constraints that are convertible to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Strict-complex constraints\", \"description\": \"Constraints that cannot be converted to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Arithmetic constraints\", \"description\": \"Constraints with at least one arithmetic operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Aggregation constraints\", \"description\": \"Constraints with at least one aggregation operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Features in constraints\", \"description\": \"Features involved in cross-tree constraints. The ratio to the total number of features is called \'Extra constraint representativeness (ECR)\'.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Video\", \"Data Storage\", \"Audio\", \"Media Player\", \"Server\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Min features per constraint\", \"description\": \"The minimal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max features per constraint\", \"description\": \"The maximal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 3, \"size\": null, \"ratio\": null}, {\"name\": \"Avg features per constraint\", \"description\": \"The average number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2.5, \"size\": null, \"ratio\": null}, {\"name\": \"Avg constraints per feature\", \"description\": \"The average number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Min constraints per feature\", \"description\": \"The minimal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Max constraints per feature\", \"description\": \"The maximal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Attributes\", \"description\": \"Features attributes in the model (i.e., number of distinct attributes).\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": null}, {\"name\": \"Features with attributes\", \"description\": \"Features that contain some attributes defined in the model.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Min attributes per feature\", \"description\": \"The minimal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Max attributes per feature\", \"description\": \"The maximal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature\", \"description\": \"Average number of attributes in features.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature w. attributes\", \"description\": \"Average number of attributes in features with attributes.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}], \"analysis\": [{\"name\": \"Satisfiable (valid)\", \"description\": \"A feature model is satisfiable (valid, not void) if it represents at least one configuration.\", \"parent\": null, \"level\": 0, \"value\": \"Yes\", \"size\": null, \"ratio\": null}, {\"name\": \"Core features\", \"description\": \"Features that are part of all the configurations (aka \'common features\').\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"False-optional features\", \"description\": \"Features included in all possible configurations although not being modelled as mandatory. The ratio is based on the total number of features.\", \"parent\": \"Core features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Dead features\", \"description\": \"Features that cannot appear in any configuration.\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Variant features\", \"description\": \"Features that appear only in some configurations (i.e., features that are neither core nor dead).\", \"parent\": null, \"level\": 0, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Configurations\", \"description\": \"Number of configurations represented by the feature model. If <= is shown, the number represents an upper estimation bound.\", \"parent\": null, \"level\": 0, \"value\": \"\\u2264 56\", \"size\": null, \"ratio\": null}, {\"name\": \"Total variability\", \"description\": \"The total variability measures the flexibility of the SPL considering all features.\", \"parent\": null, \"level\": 0, \"value\": \"5.47%\", \"size\": null, \"ratio\": null}, {\"name\": \"Partial variability\", \"description\": \"The partial variability measures the flexibility of the SPL considering only variant features.\", \"parent\": null, \"level\": 0, \"value\": \"44.09%\", \"size\": null, \"ratio\": null}]}'),
(12,'file12.uvl','checksum12',414,12,'{\"metadata\": [{\"name\": \"Name\", \"description\": \"Name of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"file12.uvl\", \"size\": null, \"ratio\": null}, {\"name\": \"Description\", \"description\": \"Description of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Description for dataset 4\", \"size\": null, \"ratio\": null}, {\"name\": \"Author\", \"description\": \"Author of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Year\", \"description\": \"Year of creation of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Reference\", \"description\": \"Main paper for reference or DOI of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Tags\", \"description\": \"Tags or keywords that identify the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"tag1\", \" tag2\"], \"size\": null, \"ratio\": null}, {\"name\": \"Domain\", \"description\": \"Domain of the feature model.\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Language level\", \"description\": \"Language level of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Boolean\", \"size\": null, \"ratio\": null}], \"metrics\": [{\"name\": \"Features\", \"description\": \"Set of features in the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": null}, {\"name\": \"Abstract features\", \"description\": \"Features used to structure the feature model that, however, do not have any impact at implementation level.\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract leaf features\", \"description\": \"Abstract and leaf features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract compound features\", \"description\": \"Abstract and compound features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Concrete features\", \"description\": \"Features that are mapped to at least one implementation artifact.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": 1.0}, {\"name\": \"Concrete leaf features\", \"description\": \"Concrete and leaf features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Concrete compound features\", \"description\": \"Concrete and compound features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Compound features\", \"description\": \"Features that have subfeatures.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Leaf features\", \"description\": \"Features that have not subfeatures (aka \'primitive features\' or \'terminal features\').\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Root feature\", \"description\": \"The root of the feature model.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\"], \"size\": 1, \"ratio\": 0.1}, {\"name\": \"Top features\", \"description\": \"Features that are first descendants of the root.\", \"parent\": \"Root feature\", \"level\": 2, \"value\": [\"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 4, \"ratio\": 0.4}, {\"name\": \"Solitary features\", \"description\": \"Features that are not grouped in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Grouped features\", \"description\": \"Features that occurs in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Typed features\", \"description\": \"Non-Boolean features its selection require to provide a value (e.g., a number, a string,...\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Numerical features\", \"description\": \"Features with a Integer or Real type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Integer features\", \"description\": \"Features with a Integer type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Real features\", \"description\": \"Features with a Real type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"String features\", \"description\": \"Features with a String type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Multi-features\", \"description\": \"Features with cardinalities (aka \'clonable features\')\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Tree relationships\", \"description\": \"Number of relationships (edges) of the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"(mandatory) Chat[1,1]Connection\", \"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(mandatory) Chat[1,1]Messages\", \"(or) Messages[1,3]Text Video Audio\", \"(optional) Chat[0,1]Data Storage\", \"(optional) Chat[0,1]Media Player\"], \"size\": 6, \"ratio\": null}, {\"name\": \"Mandatory features\", \"description\": \"Features marked as mandatory that need to be selected if its parent is selected.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Optional features\", \"description\": \"Feature marked as optional.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Feature groups\", \"description\": \"Features that express a choice over the grouped features in a group.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(or) Messages[1,3]Text Video Audio\"], \"size\": 2, \"ratio\": 0.33}, {\"name\": \"Alternative groups\", \"description\": \"Feature groups that require the selection of just one child (i.e., [1..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Or groups\", \"description\": \"Feature groups that require the selection of at least one child (i.e., [1..*] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(or) Messages[1,3]Text Video Audio\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Mutex groups\", \"description\": \"Feature groups that require the selection of zero or just one child (i.e., [0..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Cardinality groups\", \"description\": \"Feature groups with arbitraty cardinality [a..b] that require the selection of an minimum and a maximum number of children.\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Depth of tree\", \"description\": \"Number of features of the longest path from the root to the leaf features.\", \"parent\": null, \"level\": 0, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Mean depth of tree\", \"description\": \"Number of features of the mean path from the root to the leaf features.\", \"parent\": \"Depth of tree\", \"level\": 1, \"value\": 1.71, \"size\": null, \"ratio\": null}, {\"name\": \"Branching factor\", \"description\": \"Average number of children per non-leaf feature (aka \'Ratio of Variability\').\", \"parent\": null, \"level\": 0, \"value\": 3.0, \"size\": null, \"ratio\": null}, {\"name\": \"Min children per feature\", \"description\": \"Minimal number of children per non-leaf feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max children per feature\", \"description\": \"Maximal number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 4, \"size\": null, \"ratio\": null}, {\"name\": \"Avg children per feature\", \"description\": \"Average number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 0.9, \"size\": null, \"ratio\": null}, {\"name\": \"Cross-tree constraints\", \"description\": \"Textual cross-tree constraints.\", \"parent\": null, \"level\": 0, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": null}, {\"name\": \"Logical constraints\", \"description\": \"Constraints with only logical operators.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": 1.0}, {\"name\": \"Single feature constraints\", \"description\": \"Constraints with a single feature or negated feature.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Simple constraints\", \"description\": \"Requires and Excludes constraints.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Requires constraints\", \"description\": \"Constraints modeling that the activation of a feature f1 implies the activation of a feature f2.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Excludes constraints\", \"description\": \"Constraints modeling that two features are mutually exclusive and cannot be activated together.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Complex constraints\", \"description\": \"Constraints in arbitrary propositional logic formulae.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Pseudo-complex constraints\", \"description\": \"Constraints that are convertible to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Strict-complex constraints\", \"description\": \"Constraints that cannot be converted to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Arithmetic constraints\", \"description\": \"Constraints with at least one arithmetic operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Aggregation constraints\", \"description\": \"Constraints with at least one aggregation operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Features in constraints\", \"description\": \"Features involved in cross-tree constraints. The ratio to the total number of features is called \'Extra constraint representativeness (ECR)\'.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Video\", \"Data Storage\", \"Audio\", \"Media Player\", \"Server\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Min features per constraint\", \"description\": \"The minimal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max features per constraint\", \"description\": \"The maximal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 3, \"size\": null, \"ratio\": null}, {\"name\": \"Avg features per constraint\", \"description\": \"The average number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2.5, \"size\": null, \"ratio\": null}, {\"name\": \"Avg constraints per feature\", \"description\": \"The average number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Min constraints per feature\", \"description\": \"The minimal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Max constraints per feature\", \"description\": \"The maximal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Attributes\", \"description\": \"Features attributes in the model (i.e., number of distinct attributes).\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": null}, {\"name\": \"Features with attributes\", \"description\": \"Features that contain some attributes defined in the model.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Min attributes per feature\", \"description\": \"The minimal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Max attributes per feature\", \"description\": \"The maximal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature\", \"description\": \"Average number of attributes in features.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature w. attributes\", \"description\": \"Average number of attributes in features with attributes.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}], \"analysis\": [{\"name\": \"Satisfiable (valid)\", \"description\": \"A feature model is satisfiable (valid, not void) if it represents at least one configuration.\", \"parent\": null, \"level\": 0, \"value\": \"Yes\", \"size\": null, \"ratio\": null}, {\"name\": \"Core features\", \"description\": \"Features that are part of all the configurations (aka \'common features\').\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"False-optional features\", \"description\": \"Features included in all possible configurations although not being modelled as mandatory. The ratio is based on the total number of features.\", \"parent\": \"Core features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Dead features\", \"description\": \"Features that cannot appear in any configuration.\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Variant features\", \"description\": \"Features that appear only in some configurations (i.e., features that are neither core nor dead).\", \"parent\": null, \"level\": 0, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Configurations\", \"description\": \"Number of configurations represented by the feature model. If <= is shown, the number represents an upper estimation bound.\", \"parent\": null, \"level\": 0, \"value\": \"\\u2264 56\", \"size\": null, \"ratio\": null}, {\"name\": \"Total variability\", \"description\": \"The total variability measures the flexibility of the SPL considering all features.\", \"parent\": null, \"level\": 0, \"value\": \"5.47%\", \"size\": null, \"ratio\": null}, {\"name\": \"Partial variability\", \"description\": \"The partial variability measures the flexibility of the SPL considering only variant features.\", \"parent\": null, \"level\": 0, \"value\": \"44.09%\", \"size\": null, \"ratio\": null}]}'),
(13,'file4.uvl','edbbcabaafb33ee4babe5e47b5d8bfd9fd39c8a4d4bfba70571fe1148a1dd6c3',414,13,'{\"metadata\": [{\"name\": \"Name\", \"description\": \"Name of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"file4.uvl\", \"size\": null, \"ratio\": null}, {\"name\": \"Description\", \"description\": \"Description of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"sdfgsdgf\", \"size\": null, \"ratio\": null}, {\"name\": \"Author\", \"description\": \"Author of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Year\", \"description\": \"Year of creation of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Reference\", \"description\": \"Main paper for reference or DOI of the feature model\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Tags\", \"description\": \"Tags or keywords that identify the feature model.\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": null, \"ratio\": null}, {\"name\": \"Domain\", \"description\": \"Domain of the feature model.\", \"parent\": null, \"level\": 0, \"value\": null, \"size\": null, \"ratio\": null}, {\"name\": \"Language level\", \"description\": \"Language level of the feature model.\", \"parent\": null, \"level\": 0, \"value\": \"Boolean\", \"size\": null, \"ratio\": null}], \"metrics\": [{\"name\": \"Features\", \"description\": \"Set of features in the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": null}, {\"name\": \"Abstract features\", \"description\": \"Features used to structure the feature model that, however, do not have any impact at implementation level.\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract leaf features\", \"description\": \"Abstract and leaf features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Abstract compound features\", \"description\": \"Abstract and compound features.\", \"parent\": \"Abstract features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Concrete features\", \"description\": \"Features that are mapped to at least one implementation artifact.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Peer 2 Peer\", \"Server\", \"Messages\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 10, \"ratio\": 1.0}, {\"name\": \"Concrete leaf features\", \"description\": \"Concrete and leaf features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Concrete compound features\", \"description\": \"Concrete and compound features.\", \"parent\": \"Concrete features\", \"level\": 2, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Compound features\", \"description\": \"Features that have subfeatures.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"Leaf features\", \"description\": \"Features that have not subfeatures (aka \'primitive features\' or \'terminal features\').\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Root feature\", \"description\": \"The root of the feature model.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\"], \"size\": 1, \"ratio\": 0.1}, {\"name\": \"Top features\", \"description\": \"Features that are first descendants of the root.\", \"parent\": \"Root feature\", \"level\": 2, \"value\": [\"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 4, \"ratio\": 0.4}, {\"name\": \"Solitary features\", \"description\": \"Features that are not grouped in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Chat\", \"Connection\", \"Messages\", \"Data Storage\", \"Media Player\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Grouped features\", \"description\": \"Features that occurs in a feature group.\", \"parent\": \"Features\", \"level\": 1, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Typed features\", \"description\": \"Non-Boolean features its selection require to provide a value (e.g., a number, a string,...\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Numerical features\", \"description\": \"Features with a Integer or Real type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Integer features\", \"description\": \"Features with a Integer type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Real features\", \"description\": \"Features with a Real type.\", \"parent\": \"Numerical features\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"String features\", \"description\": \"Features with a String type.\", \"parent\": \"Typed features\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Multi-features\", \"description\": \"Features with cardinalities (aka \'clonable features\')\", \"parent\": \"Features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Tree relationships\", \"description\": \"Number of relationships (edges) of the feature model.\", \"parent\": null, \"level\": 0, \"value\": [\"(mandatory) Chat[1,1]Connection\", \"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(mandatory) Chat[1,1]Messages\", \"(or) Messages[1,3]Text Video Audio\", \"(optional) Chat[0,1]Data Storage\", \"(optional) Chat[0,1]Media Player\"], \"size\": 6, \"ratio\": null}, {\"name\": \"Mandatory features\", \"description\": \"Features marked as mandatory that need to be selected if its parent is selected.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Optional features\", \"description\": \"Feature marked as optional.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"Chat\", \"Chat\"], \"size\": 2, \"ratio\": 0.4}, {\"name\": \"Feature groups\", \"description\": \"Features that express a choice over the grouped features in a group.\", \"parent\": \"Tree relationships\", \"level\": 1, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\", \"(or) Messages[1,3]Text Video Audio\"], \"size\": 2, \"ratio\": 0.33}, {\"name\": \"Alternative groups\", \"description\": \"Feature groups that require the selection of just one child (i.e., [1..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(alternative) Connection[1,1]Peer 2 Peer Server\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Or groups\", \"description\": \"Feature groups that require the selection of at least one child (i.e., [1..*] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [\"(or) Messages[1,3]Text Video Audio\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Mutex groups\", \"description\": \"Feature groups that require the selection of zero or just one child (i.e., [0..1] cardinality).\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Cardinality groups\", \"description\": \"Feature groups with arbitraty cardinality [a..b] that require the selection of an minimum and a maximum number of children.\", \"parent\": \"Feature groups\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Depth of tree\", \"description\": \"Number of features of the longest path from the root to the leaf features.\", \"parent\": null, \"level\": 0, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Mean depth of tree\", \"description\": \"Number of features of the mean path from the root to the leaf features.\", \"parent\": \"Depth of tree\", \"level\": 1, \"value\": 1.71, \"size\": null, \"ratio\": null}, {\"name\": \"Branching factor\", \"description\": \"Average number of children per non-leaf feature (aka \'Ratio of Variability\').\", \"parent\": null, \"level\": 0, \"value\": 3.0, \"size\": null, \"ratio\": null}, {\"name\": \"Min children per feature\", \"description\": \"Minimal number of children per non-leaf feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max children per feature\", \"description\": \"Maximal number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 4, \"size\": null, \"ratio\": null}, {\"name\": \"Avg children per feature\", \"description\": \"Average number of children per feature.\", \"parent\": \"Branching factor\", \"level\": 1, \"value\": 0.9, \"size\": null, \"ratio\": null}, {\"name\": \"Cross-tree constraints\", \"description\": \"Textual cross-tree constraints.\", \"parent\": null, \"level\": 0, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": null}, {\"name\": \"Logical constraints\", \"description\": \"Constraints with only logical operators.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Server IMPLIES Data Storage\", \"(Video OR Audio) IMPLIES Media Player\"], \"size\": 2, \"ratio\": 1.0}, {\"name\": \"Single feature constraints\", \"description\": \"Constraints with a single feature or negated feature.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Simple constraints\", \"description\": \"Requires and Excludes constraints.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Requires constraints\", \"description\": \"Constraints modeling that the activation of a feature f1 implies the activation of a feature f2.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [\"Server IMPLIES Data Storage\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Excludes constraints\", \"description\": \"Constraints modeling that two features are mutually exclusive and cannot be activated together.\", \"parent\": \"Simple constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Complex constraints\", \"description\": \"Constraints in arbitrary propositional logic formulae.\", \"parent\": \"Logical constraints\", \"level\": 2, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 0.5}, {\"name\": \"Pseudo-complex constraints\", \"description\": \"Constraints that are convertible to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [\"(Video OR Audio) IMPLIES Media Player\"], \"size\": 1, \"ratio\": 1.0}, {\"name\": \"Strict-complex constraints\", \"description\": \"Constraints that cannot be converted to a set of simple constraints.\", \"parent\": \"Complex constraints\", \"level\": 3, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Arithmetic constraints\", \"description\": \"Constraints with at least one arithmetic operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Aggregation constraints\", \"description\": \"Constraints with at least one aggregation operator.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Features in constraints\", \"description\": \"Features involved in cross-tree constraints. The ratio to the total number of features is called \'Extra constraint representativeness (ECR)\'.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": [\"Video\", \"Data Storage\", \"Audio\", \"Media Player\", \"Server\"], \"size\": 5, \"ratio\": 0.5}, {\"name\": \"Min features per constraint\", \"description\": \"The minimal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2, \"size\": null, \"ratio\": null}, {\"name\": \"Max features per constraint\", \"description\": \"The maximal number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 3, \"size\": null, \"ratio\": null}, {\"name\": \"Avg features per constraint\", \"description\": \"The average number of features involved per cross-tree constraint.\", \"parent\": \"Features in constraints\", \"level\": 2, \"value\": 2.5, \"size\": null, \"ratio\": null}, {\"name\": \"Avg constraints per feature\", \"description\": \"The average number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Min constraints per feature\", \"description\": \"The minimal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Max constraints per feature\", \"description\": \"The maximal number of constraints per feature.\", \"parent\": \"Cross-tree constraints\", \"level\": 1, \"value\": 1, \"size\": null, \"ratio\": null}, {\"name\": \"Attributes\", \"description\": \"Features attributes in the model (i.e., number of distinct attributes).\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": null}, {\"name\": \"Features with attributes\", \"description\": \"Features that contain some attributes defined in the model.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Min attributes per feature\", \"description\": \"The minimal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Max attributes per feature\", \"description\": \"The maximal number of attributes in a feature.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature\", \"description\": \"Average number of attributes in features.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}, {\"name\": \"Avg attributes per feature w. attributes\", \"description\": \"Average number of attributes in features with attributes.\", \"parent\": \"Attributes\", \"level\": 1, \"value\": 0, \"size\": null, \"ratio\": null}], \"analysis\": [{\"name\": \"Satisfiable (valid)\", \"description\": \"A feature model is satisfiable (valid, not void) if it represents at least one configuration.\", \"parent\": null, \"level\": 0, \"value\": \"Yes\", \"size\": null, \"ratio\": null}, {\"name\": \"Core features\", \"description\": \"Features that are part of all the configurations (aka \'common features\').\", \"parent\": null, \"level\": 0, \"value\": [\"Chat\", \"Connection\", \"Messages\"], \"size\": 3, \"ratio\": 0.3}, {\"name\": \"False-optional features\", \"description\": \"Features included in all possible configurations although not being modelled as mandatory. The ratio is based on the total number of features.\", \"parent\": \"Core features\", \"level\": 1, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Dead features\", \"description\": \"Features that cannot appear in any configuration.\", \"parent\": null, \"level\": 0, \"value\": [], \"size\": 0, \"ratio\": 0.0}, {\"name\": \"Variant features\", \"description\": \"Features that appear only in some configurations (i.e., features that are neither core nor dead).\", \"parent\": null, \"level\": 0, \"value\": [\"Peer 2 Peer\", \"Server\", \"Text\", \"Video\", \"Audio\", \"Data Storage\", \"Media Player\"], \"size\": 7, \"ratio\": 0.7}, {\"name\": \"Configurations\", \"description\": \"Number of configurations represented by the feature model. If <= is shown, the number represents an upper estimation bound.\", \"parent\": null, \"level\": 0, \"value\": \"\\u2264 56\", \"size\": null, \"ratio\": null}, {\"name\": \"Total variability\", \"description\": \"The total variability measures the flexibility of the SPL considering all features.\", \"parent\": null, \"level\": 0, \"value\": \"5.47%\", \"size\": null, \"ratio\": null}, {\"name\": \"Partial variability\", \"description\": \"The partial variability measures the flexibility of the SPL considering only variant features.\", \"parent\": null, \"level\": 0, \"value\": \"44.09%\", \"size\": null, \"ratio\": null}]}');
/*!40000 ALTER TABLE `hubfiles` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `orcid`
--

DROP TABLE IF EXISTS `orcid`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `orcid` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `orcid_id` varchar(19) NOT NULL,
  `registration_date` datetime NOT NULL,
  `profile_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `orcid_id` (`orcid_id`),
  UNIQUE KEY `profile_id` (`profile_id`),
  CONSTRAINT `orcid_ibfk_1` FOREIGN KEY (`profile_id`) REFERENCES `user_profile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `orcid`
--

LOCK TABLES `orcid` WRITE;
/*!40000 ALTER TABLE `orcid` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `orcid` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `reset_token`
--

DROP TABLE IF EXISTS `reset_token`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `reset_token` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(256) NOT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `reset_token`
--

LOCK TABLES `reset_token` WRITE;
/*!40000 ALTER TABLE `reset_token` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `reset_token` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `statistics`
--

DROP TABLE IF EXISTS `statistics`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `statistics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `datasets_viewed` int(11) DEFAULT NULL,
  `feature_models_viewed` int(11) DEFAULT NULL,
  `datasets_downloaded` int(11) DEFAULT NULL,
  `feature_models_downloaded` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `statistics`
--

LOCK TABLES `statistics` WRITE;
/*!40000 ALTER TABLE `statistics` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `statistics` VALUES
(1,3,0,0,1);
/*!40000 ALTER TABLE `statistics` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(256) DEFAULT NULL,
  `password` varchar(256) NOT NULL,
  `created_at` datetime NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user`
--

LOCK TABLES `user` WRITE;
/*!40000 ALTER TABLE `user` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `user` VALUES
(1,'user1@example.com','scrypt:32768:8:1$nQ99DG6NQShIojzO$edf7027591e749a1b6a534b64e49dd695a9ffc4c0105653009579ecd7d9614213b143c7d4c36a339d539e345fdf2e65d696974655de12e75b89ffb55e8c313c7','2025-12-16 11:23:56',1),
(2,'user2@example.com','scrypt:32768:8:1$0uBKTmdgyTjXPPKO$f226c6a1ec53b8de0646885b99c805e48ee7e7234151e02a207d50412329cc15337c00862fbd832efc0d4be21d4651e67c2e474d40cc1cd14b18967e776dc9a1','2025-12-16 11:23:56',1);
/*!40000 ALTER TABLE `user` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `user_profile`
--

DROP TABLE IF EXISTS `user_profile`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_profile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `affiliation` varchar(100) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=3 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_profile`
--

LOCK TABLES `user_profile` WRITE;
/*!40000 ALTER TABLE `user_profile` DISABLE KEYS */;
set autocommit=0;
INSERT INTO `user_profile` VALUES
(1,1,'Some University','John','Doe'),
(2,2,'Some University','Jane','Doe');
/*!40000 ALTER TABLE `user_profile` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `webhook`
--

DROP TABLE IF EXISTS `webhook`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `webhook` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `webhook`
--

LOCK TABLES `webhook` WRITE;
/*!40000 ALTER TABLE `webhook` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `webhook` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Table structure for table `zenodo`
--

DROP TABLE IF EXISTS `zenodo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `zenodo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `zenodo`
--

LOCK TABLES `zenodo` WRITE;
/*!40000 ALTER TABLE `zenodo` DISABLE KEYS */;
set autocommit=0;
/*!40000 ALTER TABLE `zenodo` ENABLE KEYS */;
UNLOCK TABLES;
commit;

--
-- Dumping routines for database 'uvlhubdb'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*M!100616 SET NOTE_VERBOSITY=@OLD_NOTE_VERBOSITY */;

-- Dump completed on 2025-12-16 12:10:51
