/*
 * Copyright (C) 2010 Ulteo SAS
 * http://www.ulteo.com
 * Author Thomas MOUTON <thomas@ulteo.com> 2010
 * Author Guillaume DUPAS <guillaume@ulteo.com> 2010
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

package org.ulteo.ovd.client;

import java.awt.Container;
import java.util.ArrayList;
import java.util.HashMap;
import net.propero.rdp.RdpConnection;
import net.propero.rdp.RdpListener;
import org.apache.log4j.Logger;
import org.ulteo.ovd.OvdException;
import org.ulteo.ovd.client.authInterface.AuthFrame;
import org.ulteo.ovd.client.authInterface.LoginListener;
import org.ulteo.ovd.sm.SessionManagerCommunication;
import org.ulteo.rdp.RdpActions;
import org.ulteo.rdp.RdpConnectionOvd;

public abstract class OvdClient extends Thread implements RdpListener, RdpActions {
	public static final String productName = "OVD Client";

	public static HashMap<String,String> toMap(String login_, String password_) {
		HashMap<String,String> map = new HashMap<String, String>();

		map.put(SessionManagerCommunication.FIELD_LOGIN, login_);
		map.put(SessionManagerCommunication.FIELD_PASSWORD, password_);

		return map;
	}

	protected Logger logger = Logger.getLogger(OvdClient.class);

	protected String fqdn = null;
	protected HashMap<String,String> params = null;
	protected boolean graphic = false;

	protected AuthFrame frame = null;
	protected LoginListener logList = null;
	protected boolean isCancelled = false;

	protected SessionManagerCommunication smComm = null;
	protected ArrayList<RdpConnectionOvd> availableConnections = null;

	public OvdClient(String fqdn_, HashMap<String,String> params_) {
		this.initMembers(fqdn_, params_, false);
	}

	public OvdClient(String fqdn_, HashMap<String,String> params_, AuthFrame frame_, LoginListener logList_) {
		this.initMembers(fqdn_, params_, true);
		this.frame = frame_;
		this.logList = logList_;
	}

	private void initMembers(String fqdn_, HashMap<String,String> params_, boolean graphic_) {
		this.fqdn = fqdn_;
		this.params = params_;
		this.graphic = graphic_;

		this.availableConnections = new ArrayList<RdpConnectionOvd>();
	}

	protected void setSessionMode(String sessionMode_) {
		this.params.put(SessionManagerCommunication.FIELD_SESSION_MODE, sessionMode_);
	}

	private void addAvailableConnection(RdpConnectionOvd rc) {
		this.availableConnections.add(rc);
	}

	private void removeAvailableConnection(RdpConnectionOvd rc) {
		this.availableConnections.remove(rc);
	}

	private int countAvailableConnection() {
		return this.availableConnections.size();
	}

	public ArrayList<RdpConnectionOvd> getAvailableConnections() {
		return this.availableConnections;
	}

	protected boolean askSM() {
		return this.smComm.askForSession(this.params);
	}

	@Override
	public void run() {
		if (graphic)
			logList.initLoader();

		this.runInit();

		if (graphic)
			this.smComm = new SessionManagerCommunication(fqdn, logList.getLoader());
		else
			this.smComm = new SessionManagerCommunication(fqdn);
		
		if (! this.askSM())
			return;

		if (this.isCancelled) {
			this.smComm = null;
			this.quitProperly(0);
			return;
		}

		ArrayList<RdpConnectionOvd> connections = this.smComm.getConnections();
		for (RdpConnectionOvd rc : connections) {
			rc.addRdpListener(this);

			this.customizeConnection(rc);

			rc.connect();
		}

		this.runExit();
	}

	protected abstract void runInit();

	protected abstract void runExit();

	private void quit(int i) {
		this.quitProperly(i);
		System.exit(i);
	}

	protected abstract void quitProperly(int i);

	protected abstract void customizeConnection(RdpConnectionOvd co);

	protected abstract void uncustomizeConnection(RdpConnectionOvd co);

	protected abstract void display(RdpConnection co);

	protected abstract void hide(RdpConnection co);

	/* RdpListener */
	public void connected(RdpConnection co) {
		if(graphic) {
			logList.getLoader().setVisible(false);
			logList.getLoader().dispose();
			frame.setVisible(false);
			frame.dispose();
		}

		this.logger.info("Connected to "+co.getServer());
		this.addAvailableConnection((RdpConnectionOvd)co);

		this.display(co);
	}

	public void connecting(RdpConnection co) {
		this.logger.info("Connecting to "+co.getServer());

	}

	public void disconnected(RdpConnection co) {
		if (graphic) {
			if (logList.getLoader().isVisible()) {
				logList.getLoader().setVisible(false);
				logList.getLoader().dispose();
			}
			Container cp = frame.getContentPane();
			cp.removeAll();
		}

		this.uncustomizeConnection((RdpConnectionOvd) co);

		this.removeAvailableConnection((RdpConnectionOvd)co);
		this.logger.info("Disconnected from "+co.getServer());

		this.hide(co);

		if(graphic) {
			frame.init();
			frame.setDesktopLaunched(false);
		} else {
			System.exit(0);
		}
	}

	public void failed(RdpConnection co) {
		this.logger.error("Connection to "+co.getServer()+" failed");
	}

	/* RdpActions */
	public void disconnect(RdpConnection rc) {
		try {
			((RdpConnectionOvd) rc).sendLogoff();
		} catch (OvdException ex) {
			this.logger.warn(rc.getServer()+": "+ex.getMessage());
		}
	}

	public void seamlessEnabled(RdpConnection co) {}

	public void disconnectAll() {
		this.isCancelled = true;
		if(this.availableConnections != null) {
			for(RdpConnectionOvd co : this.availableConnections) {
				this.disconnect(co);
			}
		}
	}

	public void exit(int return_code) {
		this.disconnectAll();

		while (this.countAvailableConnection() > 0) {
			try {
				Thread.sleep(300);
			} catch (InterruptedException ex) {
				this.logger.error(ex);
			}
		}
		this.quit(return_code);
	}

}
