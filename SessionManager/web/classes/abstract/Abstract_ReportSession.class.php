<?php
/**
 * Copyright (C) 2009-2010 Ulteo SAS
 * http://www.ulteo.com
 * Author Gauvain Pocentek <gauvain@ulteo.com> 2009
 * Author Laurent CLOUET <laurent@ulteo.com> 2009-2010
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; version 2
 * of the License.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
 **/

require_once(dirname(__FILE__).'/../../includes/core.inc.php');

class Abstract_ReportSession {
	static $TYPE_SERVER = 0;
	static $TYPE_APPLICATION = 1;

	public static function init($prefs_) {
		Logger::debug('main', 'Starting Abstract_ReportSession::init');

		$sql_conf = $prefs_->get('general', 'sql');
		$SQL = SQL::newInstance($sql_conf);

		$sessions_history_table_structure = array(
			'id' => 'VARCHAR(255) NOT NULL', // same as session id,
			'start_stamp' => 'TIMESTAMP NOT NULL default CURRENT_TIMESTAMP',
			'stop_stamp' => 'TIMESTAMP NULL default NULL',
			'stop_why' => 'VARCHAR(16) default NULL',
			'user' => 'VARCHAR(255) NOT NULL',
			'server' => 'VARCHAR(255) NOT NULL',
			'data' => 'LONGTEXT NOT NULL');
		
		$ret = $SQL->buildTable($sql_conf['prefix'].'sessions_history', $sessions_history_table_structure, array('id'));

		if (! $ret) {
			Logger::error('main', 'Unable to create SQL table \''.$sql_conf['prefix'].'sessions_history\'');
			return false;
		}

		return true;
	}
	
	public static function load($id_) {
		Logger::debug('main', "Abstract_ReportSession::load($id_)");
		
		$report = new SessionReportItem($id_); // hoho...
		return $report;
	}
	
	public static function exists($id_) {
		Logger::debug('main', "Abstract_ReportSession::exists($id_)");
		$SQL = SQL::getInstance();
		
		$SQL->DoQuery('SELECT 1 FROM @1 WHERE @2 = %3 LIMIT 1', $SQL->prefix.'sessions_history', 'id', $id_);
		$total = $SQL->NumRows();
		return ($total == 1);
	}
	
	public static function create($report_) {
		Logger::debug('main', 'Abstract_ReportSession::create');
		
		$sql = SQL::getInstance();
		$res = $sql->DoQuery('INSERT INTO @1 (@2,@3,@4,@5) VALUES (%6,%7,%8,%9)', SESSIONS_HISTORY_TABLE, 'id', 'user', 'server', 'data',  $report_->getID(), $report_->user, $report_->server, '');
		return $res;
	}
	
	public static function update($report_) {
		Logger::debug('main', "Abstract_ReportSession::update");
		
		$SQL = SQL::getInstance();
		$report = Abstract_ReportSession::load($report_->getID());
		if (! is_object($report)) {
			Logger::debug('main', "Abstract_ReportSession::updateSession failed to load report ".$report_->getID());
			return false;
		}
		
		$ret = $SQL->DoQuery('UPDATE @1 SET @2=%3,@4=%5,@6=%7 WHERE @8 = %9 LIMIT 1', $SQL->prefix.'sessions_history',
// 			'start_stamp',
// 			'stop_stamp',
			'stop_why',  $report_->stop_why,
			'user', $report_->user,
			'server', $report_->server,
// 			'data',
			'id', $report_->getID());
		return $ret;
	}
 }