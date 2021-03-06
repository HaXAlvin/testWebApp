use iosclub;
CREATE TABLE `member_list` (
  `member_id` int unsigned UNIQUE NOT NULL AUTO_INCREMENT,
  `member_name` varchar(50) CHARACTER SET utf8mb4 NOT NULL DEFAULT 'None',
  `member_nid` varchar(50) NOT NULL DEFAULT 'None',
  `member_department` varchar(100) CHARACTER SET utf8mb4 NOT NULL DEFAULT 'None',
  `join_date` date NOT NULL DEFAULT '1001-01-01',
  `admission_year` int unsigned NOT NULL DEFAULT 0,
  `sex` varchar(1) not null DEFAULT 'N',
  `e-mail` varchar(100) not null DEFAULT 'None',
  `birth` date not null DEFAULT '1001-01-01',
  `phone` varchar(20),
  `password` varchar(150) not null,
  `manager` bool not null,
  `login_count` int unsigned not null default 0,
  PRIMARY KEY (`member_id`)
);

create table `class_state`(
	`class_state_id` int unsigned UNIQUE not null auto_increment,
	`member_id` int unsigned NOT NULL,
    `date` timestamp not null,
    `attendance` bool not null,
    `register` bool not null,
    FOREIGN KEY(`member_id`) references member_list(`member_id`),
    primary key(`class_state_id`)
);

create table `rtc_state`(
	`rtc_state_id` int unsigned UNIQUE not null auto_increment,
    `date` timestamp not null,
    `member_id` int unsigned NOT NULL,
    `access` bool not null,
    `serial_number` bigint not null,
    foreign key(`member_id`) references member_list(`member_id`),
    primary key(`rtc_state_id`)
);

create table `announcement`(
    `announcement_id` int unsigned UNIQUE not null auto_increment,
    `date` timestamp not null,
    `img_path` varchar(150) not null,
    `title` varchar(100) not null,
    `content` LongText not null,
    `view_count` int unsigned not null default 0,
    primary key (`announcement_id`)
);

create table `comment`(
    `comment_id` int not null unique auto_increment,
    `announcement_id` int unsigned not null,
    `member_id` int unsigned not null ,
    `comment_date` timestamp not null,
    `comment_content` LongText not null,
    primary key(`comment_id`),
    foreign key(`announcement_id`) references announcement(`announcement_id`),
    foreign key(`member_id`) references  member_list(`member_id`)
);

create table `day_off`(
    `day_off_id` int unsigned not null auto_increment,
    `member_id` int unsigned NOT NULL,
    `reason` LongText not null,
    `day_off_date` date not null,
    `send_time` timestamp not null,
    `day_off_type` varchar(50) CHARACTER SET utf8mb4 not null,
    `day_off_accept` tinyint not null default 0,
    `audit_manager` int unsigned,
    primary key(`day_off_id`),
    foreign key(`member_id`) references member_list(`member_id`),
    foreign key(`audit_manager`) references member_list(`member_id`)
);

create table `device_list`(
    `device_id` int unsigned not null auto_increment,
    `device_name` varchar(150) CHARACTER SET utf8mb4 not null,
    `device_update_time` date not null,
    `device_manager` varchar(100) not null ,
    `device_count` int unsigned not null,
    `device_unit` varchar(50) not null,
    `device_source` varchar(150) not null,
    `device_cost` int unsigned,
    `device_receipt` text,
    `device_remarks` mediumtext,
#     `device_location` varchar(150) not null,
    `borrowable` bool not null,
#     `borrower` int unsigned,
    primary key(`device_id`)
#     foreign key(`borrower`) references member_list(`member_id`)
);

create table `device_borrowed`(
    `borrowed_id` int unsigned not null auto_increment,
    `borrowed_start_date` date not null,
    `borrowed_end_date` date not null,
    `device_id` int unsigned not null,
    `borrowed_count` int unsigned not null,
    `borrower` int unsigned not null,
    `borrowed_reason` mediumtext not null ,
    `borrowed_accept` bool not null default 0,
    `audit_manager` int unsigned default null,
    foreign key(`borrower`) references member_list(`member_id`),
    foreign key(`audit_manager`) references member_list(`member_id`),
    foreign key(`device_id`) references device_list(`device_id`),
    primary key(borrowed_id)
);