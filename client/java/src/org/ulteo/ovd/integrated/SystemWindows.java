/*
 * Copyright (C) 2009 Ulteo SAS
 * http://www.ulteo.com
 * Author Thomas MOUTON <thomas@ulteo.com> 2010
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
 */

package org.ulteo.ovd.integrated;

import java.awt.Graphics2D;
import java.awt.image.BufferedImage;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileInputStream;
import java.io.FileNotFoundException;
import java.io.FileOutputStream;
import java.io.IOException;
import org.ulteo.Logger;
import org.ulteo.ovd.Application;
import org.ulteo.ovd.integrated.mime.WindowsRegistry;
import org.ulteo.ovd.integrated.shorcut.WindowsShortcut;

public class SystemWindows extends SystemAbstract {

	public SystemWindows() {
		this.shortcut = new WindowsShortcut();
		this.fileAssociate = new WindowsRegistry();
	}

	@Override
	public String install(Application app) {
		this.saveIcon(app);
		this.fileAssociate.createAppAction(app);
		
		String shortcutName = this.shortcut.create(app);

		if (shortcutName == null)
			return null;

		File f = new File(Constants.PATH_SHORTCUTS+Constants.FILE_SEPARATOR+shortcutName);
		if (! f.exists()) {
			Logger.error("Cannot copy the '"+shortcutName+"' shortcut: The file does not exist ("+f.getPath()+")");
			return null;
		}

		try {
			BufferedInputStream shortcutReader = new BufferedInputStream(new FileInputStream(f), 4096);
			File desktopShortcut = new File(Constants.PATH_DESKTOP+Constants.FILE_SEPARATOR+shortcutName);
			File startMenuShortcut = new File(Constants.PATH_STARTMENU+Constants.FILE_SEPARATOR+shortcutName);

			BufferedOutputStream desktopStream = new BufferedOutputStream(new FileOutputStream(desktopShortcut), 4096);
			BufferedOutputStream startMenuStream = new BufferedOutputStream(new FileOutputStream(startMenuShortcut), 4096);

			int currentChar;
			while ((currentChar = shortcutReader.read()) != -1) {
				desktopStream.write(currentChar);
				startMenuStream.write(currentChar);
			}

			desktopStream.close();
			startMenuStream.close();
			shortcutReader.close();
		} catch(FileNotFoundException e) {
			Logger.error("This file does not exists: "+e.getMessage());
			return null;
		} catch(IOException e) {
			Logger.error("An error occured during the shortcut '"+shortcutName+"' copy: "+e.getMessage());
			return null;
		}

		return shortcutName;
	}

	@Override
	public void uninstall(Application app) {
		File desktopItem = new File(Constants.PATH_DESKTOP+Constants.FILE_SEPARATOR+app.getName()+".lnk");
		if (desktopItem.exists())
			desktopItem.delete();
		desktopItem = null;

		File menuItem = new File(Constants.PATH_STARTMENU+Constants.FILE_SEPARATOR+app.getName()+".lnk");
		if (menuItem.exists())
			menuItem.delete();
		menuItem = null;

		this.shortcut.remove(app);
		this.fileAssociate.removeAppAction(app);
	}

	@Override
	protected void saveIcon(Application app) {
		File output = new File(Constants.PATH_ICONS+Constants.FILE_SEPARATOR+app.getIconName()+".ico");
		if (! output.exists()) {
			try {
				output.createNewFile();
			} catch (IOException ex) {
				Logger.error("Error while creating "+app.getName()+" icon file: "+ex.getMessage());
				return;
			}
		}
		BufferedImage buf = new BufferedImage(app.getIcon().getIconWidth(), app.getIcon().getIconHeight(), BufferedImage.TYPE_INT_RGB);
		Graphics2D graph = buf.createGraphics();
		graph.drawImage(app.getIcon().getImage(), 0, 0, null);
		graph.dispose();
		
		
		try {
			BufferedOutputStream os = new BufferedOutputStream(new FileOutputStream(output));
			net.sf.image4j.codec.ico.ICOEncoder.write(buf, os);
			os.close();
		} catch (IOException ex) {
			Logger.error("Error while converting "+app.getName()+" icon: "+ex.getMessage());
		}
	}
}
