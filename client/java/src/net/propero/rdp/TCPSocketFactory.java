/*
 * Copyright (C) 2010 Ulteo SAS
 * http://www.ulteo.com
 * Author Arnaud LEGRAND <arnaud@ulteo.com> 2010
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

package net.propero.rdp;

import java.io.IOException;
import java.net.InetAddress;
import java.net.InetSocketAddress;
import java.net.Socket;

public class TCPSocketFactory implements SocketFactory {
	private InetAddress host;
	private int port;

	public TCPSocketFactory(InetAddress host, int port) {
		this.host = host;
		this.port = port;
	}

	public Socket createSocket() throws IOException, RdesktopException {
		Socket rdpsock = null;

		try {
			rdpsock = new Socket();
			rdpsock.connect(new InetSocketAddress(this.host, this.port), 3000);
		} catch (Exception e) {
			throw new RdesktopException("Creating Socket failed:" + e.getMessage());
		}
		
		return rdpsock;
	}
}
