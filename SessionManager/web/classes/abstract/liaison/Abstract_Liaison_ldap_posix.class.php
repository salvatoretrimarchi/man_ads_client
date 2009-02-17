<?php
/**
 * Copyright (C) 2009 Ulteo SAS
 * http://www.ulteo.com
 * Author Laurent CLOUET <laurent@ulteo.com>
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
require_once(dirname(__FILE__).'/../../../includes/core.inc.php');

class Abstract_Liaison_ldap_posix {
	public static function load($type_, $element_=NULL, $group_=NULL) {
		Logger::debug('admin',"Abstract_Liaison_ldap_posix::load($type_,$element_,$group_)");
		if ($type_ == 'UsersGroup') {
			if (is_null($element_) && is_null($group_))
				return self::loadAll($type_);
			else if (is_null($element_))
				return self::loadElements($type_, $group_);
			else if (is_null($group_))
				return self::loadGroups($type_, $element_);
			else
				return self::loadUnique($type_, $element_, $group_);
		}
		else
		{
			Logger::error('admin',"Abstract_Liaison_ldap_posix::load error liaison != UsersGroup not implemented");
			return NULL;
		}
		return NULL;
		
	}
	public function save($type_, $element_, $group_) {
		Logger::debug('admin',"<b>Abstract_Liaison_ldap_posix::save</b>");
		return false;
	}
	public function delete($type_, $element_, $group_) {
		Logger::debug('admin',"<b>Abstract_Liaison_ldap_posix::delete</b>");
		return false;
	}
	public function loadElements($type_, $group_) {
		Logger::debug('admin',"<b>Abstract_Liaison_ldap_posix::loadElements ($type_,$group_)</b>");
		
		$prefs = Preferences::getInstance();
		if (! $prefs)
			die_error('get Preferences failed',__FILE__,__LINE__);
		
		$mods_enable = $prefs->get('general','module_enable');
		if (! in_array('UserGroupDB',$mods_enable))
			die_error(_('Module UserGroupDB must be enabled'),__FILE__,__LINE__);
		if (! in_array('UserDB',$mods_enable))
			die_error(_('Module UserDB must be enabled'),__FILE__,__LINE__);
		
		$mod_usergroup_name = 'UserGroupDB_'.$prefs->get('UserGroupDB','enable');
		$userGroupDB = new $mod_usergroup_name();
		$mod_user_name = 'UserDB_'.$prefs->get('UserDB','enable');
		$userDB = new $mod_user_name();
		
		$configLDAP = $prefs->get('UserDB','ldap');
		$configLDAP['userbranch'] = 'ou=Group';
		
		$ldap = new LDAP($configLDAP);
		$sr = $ldap->search('cn='.$group_, NULL);
		$infos = $ldap->get_entries($sr);
		if (!is_array($infos))
			return NULL;
		$info = $infos[0];
		if ( isset($info['dn']) && $info['cn']) {
			if (is_string($info['dn']) && isset($info['cn']) && is_array($info['cn']) && isset($info['cn'][0]) ) {
				$u = new UsersGroup($info['cn'][0], $info['cn'][0], '', true);
				if ($userGroupDB->isOK($u)) {
					$elements = array();
					if (isset($info['memberuid'])) {
						unset($info['memberuid']['count']);
						foreach ($info['memberuid'] as $memberuid) {
							$u = $userDB->import($memberuid);
							if (is_object($u)) {
								$l = new Liaison($u->getAttribute('login'), $group_);
								$elements[$l->element] = $l;
							}
						}
					}
					return $elements;
				}
			}
		}
		return NULL;
	}
	
	public function loadGroups($type_, $element_) {
		Logger::debug('admin',"<b>Abstract_Liaison_ldap_posix::loadGroups ($type_,$element_)</b>");
		
		$prefs = Preferences::getInstance();
		if (! $prefs)
			die_error('get Preferences failed',__FILE__,__LINE__);
		$mods_enable = $prefs->get('general','module_enable');
		if (! in_array('UserGroupDB',$mods_enable))
			die_error(_('Module UserGroupDB must be enabled'),__FILE__,__LINE__);
		
		if (! in_array('UserDB',$mods_enable))
			die_error(_('Module UserDB must be enabled'),__FILE__,__LINE__);
		$mod_usergroup_name = 'UserGroupDB_'.$prefs->get('UserGroupDB','enable');
		$userGroupDB = new $mod_usergroup_name();
		$mod_user_name = 'UserDB_'.$prefs->get('UserDB','enable');
		$userDB = new $mod_user_name();
		
		$groups = array();
		$groups_all = $userGroupDB->getList();
		if (! is_array($groups_all)) {
			Logger::error('main', 'Abstract_Liaison_ldap::loadGroups userGroupDB->getList failed');
			return NULL;
		}
		foreach ($groups_all as $a_group) {
			if (in_array($element_, $a_group->usersLogin())) {
				$l = new Liaison($element_,$a_group->id);
				$groups[$l->group] = $l;
			}
		}
		return $groups;
	}
	
	public function loadAll($type_) {
		Logger::debug('main',"<b>Abstract_Liaison_ldap_posix::loadAll ($type_)</b>");
		echo "Abstract_Liaison_ldap_posix::loadAll($type_)<br>";
		return NULL;
	}
	public function loadUnique($type_, $element_, $group_) {
		Logger::debug('main',"<b>Abstract_Liaison_ldap_posix::loadUnique ($type_,$element_,$group_)</b>");
		echo "Abstract_Liaison_ldap_posix::loadUnique($type_,$element_,$group_)<br>";
		return NULL;
	}
	
	public static function init($prefs_) {
		return true;
	}
}
