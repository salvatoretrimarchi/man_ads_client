<?php
/**
 * Copyright (C) 2010-2012 Ulteo SAS
 * http://www.ulteo.com
 * Author Julien LANGLOIS <julien@ulteo.com> 2010, 2012
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

class UsersList {
	protected $search_item;
	protected $search_fields;
	
	protected $result;
	protected $partial_result;
	
	
	public function __construct($array_env) {
		$this->search_item = '';
		$this->search_fields = array('login');
		
		if (array_keys_exists_not_empty(array('search_item'), $array_env) && isset($array_env['search_fields'])) {
			$this->search_item = $array_env['search_item'];
			$this->search_fields = $array_env['search_fields'];
		}
	}
	
	
	function search() {
		$res = $_SESSION['service']->users_list_partial($this->search_item, $this->search_fields);
		if ($res === null) {
			return array();
		}
		
		$users = array();
		foreach($res['data'] as $item_id => $item) {
			$user = new User($item);
			if (! $user->is_valid()) {
				continue;
			}
			
			$users[]= $user;
		}
		
		$this->partial_result = $res['partial'];
		$this->result = $users;
		
		return $this->result;
	}
	
	
	function getForm($form_params_ = array('action' => 'search')) {
		$str = '';
		$str.= '<div style="margin-bottom: 15px;">';
		$str.= '<form action="" method="GET">';
		foreach ($form_params_ as $k => $v) {
			$str.= '<input type="hidden" name="'.$k.'" value="'.$v.'"/>';
		}
		$str.= '<table><tr>';
		$str.= '<td>'._('Search for user pattern: ').'</td>';
		$str.= '<td><input type="text" name="search_item" value="'.$this->search_item.'" /> ';
		$str.= '<input type="submit" value="'._('Search').'" /><td>';
		$str.= '</tr><tr><td></td>';
		$str.= '<td>'._('Search in: ');
		$str.= '<input type="checkbox" name="search_fields[]" value="login"';
		if (in_array('login', $this->search_fields))
			$str.= ' checked="checked"';
		$str.= '>'._('Login').' ';
		$str.= '<input type="checkbox" name="search_fields[]" value="displayname"';
		if (in_array('displayname', $this->search_fields))
			$str.= ' checked="checked"';
		$str.= '>'._('Display name').' ';
		$str.= '</td></tr>';
	
		$str.= '<tr><td></td>';
		$str.= '<td>';
		if ($this->partial_result == true) {
			$str.= '<span class="error">';
			$str.= sprintf(ngettext("<strong>Partial content:</strong> Only <strong>%d result</strong> displayed but there are more. Please restrict your search field.", "<strong>Partial content:</strong> Only <strong>%d results</strong> displayed but there are more. Please restrict your search field.", count($this->result)), count($this->result));
			$str.= '</span>';
		}
		else if (strlen($this->search_item)>0)
			$str.= sprintf(ngettext('<strong>%d</strong> result for "%s".', '<strong>%d</strong> results for "%s".', count($this->result)), count($this->result), $this->search_item);
	
		$str.= '</td></tr>';
	
		$str.= '</table>';
		$str.= '</form>';
		$str.= '</div>';
	
		return $str;
	}
}