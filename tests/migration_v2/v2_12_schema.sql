-- uvlhub.io 2.12 at e5f6a7b8c9d0, made by tests/migration_v2/v2_schema.py from
-- _reference/uvlhub_monolith/migrations/versions. Do not edit by hand.
SET FOREIGN_KEY_CHECKS = 0;

CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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

CREATE TABLE `author` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `affiliation` varchar(120) DEFAULT NULL,
  `orcid` varchar(19) DEFAULT NULL,
  `ds_meta_data_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_meta_data_id` (`ds_meta_data_id`),
  CONSTRAINT `author_ibfk_1` FOREIGN KEY (`ds_meta_data_id`) REFERENCES `ds_meta_data` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dataset_rating` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `dataset_id` int(11) NOT NULL,
  `is_like` tinyint(1) NOT NULL,
  `created_at` datetime NOT NULL,
  `updated_at` datetime NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_rating_user_dataset` (`user_id`,`dataset_id`),
  KEY `ix_dataset_rating_user_id` (`user_id`),
  KEY `ix_dataset_rating_dataset_id` (`dataset_id`),
  CONSTRAINT `dataset_rating_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`) ON DELETE CASCADE,
  CONSTRAINT `dataset_rating_ibfk_2` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `dataset_transfer_request` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  `from_user_id` int(11) NOT NULL,
  `to_user_id` int(11) NOT NULL,
  `status` enum('PENDING','ACCEPTED','DECLINED','CANCELLED') NOT NULL,
  `message` varchar(500) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `resolved_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ix_dataset_transfer_request_dataset_id` (`dataset_id`),
  KEY `ix_dataset_transfer_request_from_user_id` (`from_user_id`),
  KEY `ix_dataset_transfer_request_to_user_id` (`to_user_id`),
  CONSTRAINT `dataset_transfer_request_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`) ON DELETE CASCADE,
  CONSTRAINT `dataset_transfer_request_ibfk_2` FOREIGN KEY (`from_user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `dataset_transfer_request_ibfk_3` FOREIGN KEY (`to_user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `datasets` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `ds_meta_data_id` int(11) NOT NULL,
  `created_at` datetime NOT NULL,
  `feature_model_count` int(11) NOT NULL,
  `dataset_version` int(11) NOT NULL,
  `dataset_origin_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_meta_data_id` (`ds_meta_data_id`),
  KEY `user_id` (`user_id`),
  KEY `ix_datasets_dataset_origin_id` (`dataset_origin_id`),
  CONSTRAINT `datasets_ibfk_1` FOREIGN KEY (`ds_meta_data_id`) REFERENCES `ds_meta_data` (`id`),
  CONSTRAINT `datasets_ibfk_2` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`),
  CONSTRAINT `fk_datasets_dataset_origin_id` FOREIGN KEY (`dataset_origin_id`) REFERENCES `datasets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `doi_mapping` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_doi_old` varchar(120) DEFAULT NULL,
  `dataset_doi_new` varchar(120) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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
  `metadata_synced` tinyint(1) NOT NULL DEFAULT 1,
  `dataset_concept_doi` varchar(120) DEFAULT NULL,
  `api_publisher_user_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `ds_metrics_id` (`ds_metrics_id`),
  KEY `ix_ds_meta_data_dataset_concept_doi` (`dataset_concept_doi`),
  KEY `fk_ds_meta_data_api_publisher_user_id` (`api_publisher_user_id`),
  CONSTRAINT `ds_meta_data_ibfk_1` FOREIGN KEY (`ds_metrics_id`) REFERENCES `ds_metrics` (`id`),
  CONSTRAINT `fk_ds_meta_data_api_publisher_user_id` FOREIGN KEY (`api_publisher_user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `ds_metrics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `number_of_models` int(11) DEFAULT NULL,
  `number_of_features` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `elasticsearch` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `external_identity` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `provider` varchar(50) NOT NULL,
  `provider_id` varchar(256) NOT NULL,
  `email` varchar(256) DEFAULT NULL,
  `created_at` datetime NOT NULL,
  `provider_username` varchar(256) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_provider_id` (`provider`,`provider_id`),
  KEY `ix_external_identity_user_id` (`user_id`),
  CONSTRAINT `external_identity_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `feature_model` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `dataset_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `dataset_id` (`dataset_id`),
  CONSTRAINT `feature_model_ibfk_1` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `flamapy` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `github` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `github_id` int(11) NOT NULL,
  `github_login` varchar(255) NOT NULL,
  `registration_date` datetime NOT NULL,
  `profile_id` int(11) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `github_id` (`github_id`),
  UNIQUE KEY `profile_id` (`profile_id`),
  UNIQUE KEY `ix_github_github_id` (`github_id`),
  UNIQUE KEY `ix_github_profile_id` (`profile_id`),
  CONSTRAINT `github_ibfk_1` FOREIGN KEY (`profile_id`) REFERENCES `user_profile` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `hubfile_factlabel` (
  `hubfile_id` int(11) NOT NULL,
  `factlabel_json` text DEFAULT NULL,
  PRIMARY KEY (`hubfile_id`),
  CONSTRAINT `hubfile_factlabel_ibfk_1` FOREIGN KEY (`hubfile_id`) REFERENCES `hubfiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `hubfile_metrics` (
  `hubfile_id` int(11) NOT NULL,
  `extracted_at` datetime NOT NULL,
  `extractor_version` varchar(20) NOT NULL,
  `parse_error` text DEFAULT NULL,
  `features` int(11) DEFAULT NULL,
  `abstract_features` int(11) DEFAULT NULL,
  `concrete_features` int(11) DEFAULT NULL,
  `leaf_features` int(11) DEFAULT NULL,
  `compound_features` int(11) DEFAULT NULL,
  `top_features` int(11) DEFAULT NULL,
  `solitary_features` int(11) DEFAULT NULL,
  `grouped_features` int(11) DEFAULT NULL,
  `typed_features` int(11) DEFAULT NULL,
  `multi_features` int(11) DEFAULT NULL,
  `tree_relationships` int(11) DEFAULT NULL,
  `mandatory_features` int(11) DEFAULT NULL,
  `optional_features` int(11) DEFAULT NULL,
  `feature_groups` int(11) DEFAULT NULL,
  `alternative_groups` int(11) DEFAULT NULL,
  `or_groups` int(11) DEFAULT NULL,
  `mutex_groups` int(11) DEFAULT NULL,
  `cardinality_groups` int(11) DEFAULT NULL,
  `depth_of_tree` int(11) DEFAULT NULL,
  `mean_depth_of_tree` float DEFAULT NULL,
  `branching_factor` float DEFAULT NULL,
  `min_children_per_feature` int(11) DEFAULT NULL,
  `max_children_per_feature` int(11) DEFAULT NULL,
  `avg_children_per_feature` float DEFAULT NULL,
  `cross_tree_constraints` int(11) DEFAULT NULL,
  `logical_constraints` int(11) DEFAULT NULL,
  `simple_constraints` int(11) DEFAULT NULL,
  `requires_constraints` int(11) DEFAULT NULL,
  `excludes_constraints` int(11) DEFAULT NULL,
  `complex_constraints` int(11) DEFAULT NULL,
  `pseudo_complex_constraints` int(11) DEFAULT NULL,
  `strict_complex_constraints` int(11) DEFAULT NULL,
  `arithmetic_constraints` int(11) DEFAULT NULL,
  `aggregation_constraints` int(11) DEFAULT NULL,
  `features_in_constraints` int(11) DEFAULT NULL,
  `avg_features_per_constraint` float DEFAULT NULL,
  `avg_constraints_per_feature` float DEFAULT NULL,
  `satisfiable` tinyint(1) DEFAULT NULL,
  `core_features` int(11) DEFAULT NULL,
  `false_optional_features` int(11) DEFAULT NULL,
  `dead_features` int(11) DEFAULT NULL,
  `variant_features` int(11) DEFAULT NULL,
  `unique_features` int(11) DEFAULT NULL,
  `pure_optional_features` int(11) DEFAULT NULL,
  `configurations` double DEFAULT NULL,
  `configurations_is_upper_bound` tinyint(1) DEFAULT NULL,
  `total_variability` float DEFAULT NULL,
  `partial_variability` float DEFAULT NULL,
  `homogeneity` float DEFAULT NULL,
  `cfg_mean_features` float DEFAULT NULL,
  `cfg_stddev_features` float DEFAULT NULL,
  `cfg_median_features` float DEFAULT NULL,
  `cfg_min_features` int(11) DEFAULT NULL,
  `cfg_max_features` int(11) DEFAULT NULL,
  PRIMARY KEY (`hubfile_id`),
  KEY `ix_hubfile_metrics_satisfiable` (`satisfiable`),
  KEY `ix_hubfile_metrics_features` (`features`),
  CONSTRAINT `hubfile_metrics_ibfk_1` FOREIGN KEY (`hubfile_id`) REFERENCES `hubfiles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `hubfiles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(120) NOT NULL,
  `checksum` varchar(120) NOT NULL,
  `size` int(11) NOT NULL,
  `feature_model_id` int(11) NOT NULL,
  `dataset_id` int(11) NOT NULL,
  `directory_path` varchar(255) NOT NULL DEFAULT '',
  PRIMARY KEY (`id`),
  KEY `feature_model_id` (`feature_model_id`),
  KEY `ix_hubfiles_dataset_id` (`dataset_id`),
  CONSTRAINT `fk_hubfiles_dataset_id` FOREIGN KEY (`dataset_id`) REFERENCES `datasets` (`id`),
  CONSTRAINT `hubfiles_ibfk_1` FOREIGN KEY (`feature_model_id`) REFERENCES `feature_model` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

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

CREATE TABLE `reset_token` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `token` varchar(256) NOT NULL,
  `used_at` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `token` (`token`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `statistics` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `datasets_viewed` int(11) DEFAULT NULL,
  `feature_models_viewed` int(11) DEFAULT NULL,
  `datasets_downloaded` int(11) DEFAULT NULL,
  `feature_models_downloaded` int(11) DEFAULT NULL,
  `datasets_counter` int(11) DEFAULT 0,
  `feature_models_counter` int(11) DEFAULT 0,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `user` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `email` varchar(256) DEFAULT NULL,
  `password` varchar(256) NOT NULL,
  `created_at` datetime NOT NULL,
  `active` tinyint(1) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `email` (`email`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `user_profile` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `affiliation` varchar(100) DEFAULT NULL,
  `name` varchar(100) NOT NULL,
  `surname` varchar(100) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `user_id` (`user_id`),
  CONSTRAINT `user_profile_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `webhook` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

CREATE TABLE `zenodo` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_uca1400_ai_ci;

SET FOREIGN_KEY_CHECKS = 1;
