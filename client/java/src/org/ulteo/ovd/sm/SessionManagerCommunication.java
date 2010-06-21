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

package org.ulteo.ovd.sm;

import java.awt.Dimension;
import java.awt.GraphicsEnvironment;
import java.awt.Rectangle;
import java.awt.Toolkit;
//import java.io.BufferedReader;
//import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
//import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.net.HttpURLConnection;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.logging.Level;
import java.util.logging.Logger;

import javax.swing.JDialog;
import javax.swing.JOptionPane;
import javax.xml.parsers.DocumentBuilderFactory;
import javax.xml.parsers.ParserConfigurationException;
import net.propero.rdp.RdesktopException;
import org.ulteo.ovd.Application;
import org.ulteo.rdp.RdpConnectionOvd;
import org.w3c.dom.Document;
import org.w3c.dom.Element;
import org.w3c.dom.NodeList;
import org.xml.sax.SAXException;


public class SessionManagerCommunication {
	public static final String SESSION_MODE_REMOTEAPPS = "applications";
	public static final String SESSION_MODE_DESKTOP = "desktop";

	public static final String WEBSERVICE_START_SESSION = "startsession.php";
	public static final String WEBSERVICE_EXTERNAL_APPS = "client/remote_apps.php";

	public static final String FIELD_LOGIN = "login";
	public static final String FIELD_PASSWORD = "password";
	public static final String FIELD_TOKEN = "token";
	public static final String FIELD_SESSION_MODE = "session_mode";

	private String sm = null;
	private ArrayList<RdpConnectionOvd> connections = null;
	private String sessionMode = null;
	private String requestMode = null;
	private String sessionId = null;
	private String base_url;
	private JDialog loadFrame = null;
	private boolean graphic = false;
	private String multimedia = null;
	private String printers = null;

	public SessionManagerCommunication(String sm_, JDialog loadFrame) {
		this.connections = new ArrayList<RdpConnectionOvd>();
		this.sm = sm_;
		this.base_url = "http://"+this.sm+"/sessionmanager/";
		this.loadFrame = loadFrame;
		this.graphic = true;
	}

	public SessionManagerCommunication(String sm_) {
		this.connections = new ArrayList<RdpConnectionOvd>();
		this.sm = sm_;
		this.base_url = "http://"+this.sm+"/sessionmanager/";
	}
	public String getSessionMode() {
		return this.sessionMode;
	}

	private static String makeStringForPost(List<String> listParameter) {
		String listConcat = "";
		if(listParameter.size() > 0) {
			listConcat += listParameter.get(0);
			for(int i = 1 ; i < listParameter.size() ; i++) {
				listConcat += "&";
				listConcat += listParameter.get(i);
			}
		}
		return listConcat;
	}

	public boolean askForSession(HashMap<String,String> params) {
		if (params == null)
			return false;

		if ((! params.containsKey(FIELD_LOGIN)) || (! params.containsKey(FIELD_PASSWORD)) || (! params.containsKey(FIELD_SESSION_MODE))) {
			System.err.println("ERROR: some askForSession required arguments are missing");
			return false;
		}

		this.requestMode = params.get(FIELD_SESSION_MODE);

		return this.askWebservice(WEBSERVICE_START_SESSION, params);
	}

	public boolean askForApplications(HashMap<String,String> params) {
		this.requestMode = SESSION_MODE_REMOTEAPPS;

		if (! params.containsKey(FIELD_TOKEN)) {
			System.err.println("ERROR: some askForApplications required arguments are missing");
			return false;
		}

		if (params.containsKey(FIELD_SESSION_MODE) && (! params.get(FIELD_SESSION_MODE).equals(SESSION_MODE_REMOTEAPPS))) {
			System.out.println("Overriding session mode");
			params.remove(FIELD_SESSION_MODE);
		}
		if (! params.containsKey(FIELD_SESSION_MODE))
			params.put(FIELD_SESSION_MODE, this.requestMode);

		return this.askWebservice(WEBSERVICE_EXTERNAL_APPS, params);
	}

	private boolean askWebservice(String webservice, HashMap<String,String> params) {
		boolean ret = false;
		HttpURLConnection connexion = null;
		
		try {
			URL url = new URL(this.base_url+webservice);

			System.out.println("Connexion a l'url ... "+url);
			connexion = (HttpURLConnection) url.openConnection();
			connexion.setDoInput(true);
			connexion.setDoOutput(true);
			connexion.setRequestProperty("Content-type", "application/x-www-form-urlencoded");

			connexion.setAllowUserInteraction(true);
			connexion.setRequestMethod("POST");

			OutputStreamWriter out = new OutputStreamWriter(connexion.getOutputStream());

			List<String> listParameter = new ArrayList<String>();
			for (String name : params.keySet()) {
				listParameter.add(name+"="+params.get(name));
			}

			out.write(makeStringForPost(listParameter));
			out.flush();
			out.close();

			int r = connexion.getResponseCode();
			String res = connexion.getResponseMessage();
			String contentType = connexion.getContentType();

			System.out.println("Response "+r+ " ==> "+res+ " type: "+contentType);

			if (r == HttpURLConnection.HTTP_OK && contentType.startsWith("text/xml")) {
				DataInputStream in = new DataInputStream(connexion.getInputStream());
				ret = this.parse(in);
			}
			else {
				System.err.println("Invalid response");
			}
		}
		catch (Exception e) {
			System.err.println("Invalid session initialisation format");
			e.printStackTrace();
		}
		finally {
			connexion.disconnect();
		}

		return ret;
	}

	private boolean parse(InputStream in) {
		/* BEGIN DEBUG
		BufferedReader b = new BufferedReader(new InputStreamReader(in));

		String line;
		String content = "";
		try {
			while ((line = b.readLine()) != null) {
				content += line;
			}
		} catch (IOException ex) {
			Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, null, ex);
		}

		content = content.replaceFirst(".*<?xml", "<?xml");
		System.out.println("XML content: "+content);

		in = new ByteArrayInputStream(content.getBytes());
		/* END DEBUG */

		Document document = null;
		Dimension screenSize = Toolkit.getDefaultToolkit().getScreenSize();
		Rectangle dim = null;
		dim = GraphicsEnvironment.getLocalGraphicsEnvironment().getMaximumWindowBounds();
		Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.INFO, "ScreenSize: "+screenSize);

		try {
			document = DocumentBuilderFactory.newInstance().newDocumentBuilder().parse(in);
		} catch (SAXException e) {
			e.printStackTrace();
			return false;
		} catch (IOException e) {
			e.printStackTrace();
			return false;
		} catch (ParserConfigurationException e) {
			e.printStackTrace();
			return false;
		}

		NodeList ns = document.getElementsByTagName("error");
		Element ovd_node;
		if (ns.getLength() == 1) {
			ovd_node = (Element)ns.item(0);
			Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, "("+ovd_node.getAttribute("id")+") "+ovd_node.getAttribute("message"));
			if (graphic) {
				loadFrame.setVisible(false);
				JOptionPane.showMessageDialog(null, ovd_node.getAttribute("message"), "Warning", JOptionPane.WARNING_MESSAGE);
			}
			return false;
		}

		ns = document.getElementsByTagName("session");
		if (ns.getLength() == 0) {
			Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, "Bad XML: err 1");
			if (graphic) {
				loadFrame.setVisible(false);
				JOptionPane.showMessageDialog(null, "Bad XML: err 1", "Warning", JOptionPane.WARNING_MESSAGE);
			}
			return false;
		}
		ovd_node = (Element)ns.item(0);

		this.sessionId = ovd_node.getAttribute("id");
		this.sessionMode = ovd_node.getAttribute("mode");
		this.multimedia = ovd_node.getAttribute("multimedia");
		this.printers = ovd_node.getAttribute("redirect_client_printers");

		if (! this.sessionMode.equalsIgnoreCase(this.requestMode)) {
			Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, "The session manager do not authorize "+this.requestMode+" session mode.");
			if (graphic) {
				loadFrame.setVisible(false);
				JOptionPane.showMessageDialog(null, "The session manager do not authorize "+this.requestMode, "Warning", JOptionPane.WARNING_MESSAGE);
			}
			return false;
		}

		ns = ovd_node.getElementsByTagName("server");
		if (ns.getLength() == 0) {
			Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, "Bad XML: err 2");
			if (graphic) {
				loadFrame.setVisible(false);
				JOptionPane.showMessageDialog(null, "Bad XML: err 2", "Warning", JOptionPane.WARNING_MESSAGE);
			}
			return false;
		}
		Element server;
		for (int i = 0; i < ns.getLength(); i++) {
			RdpConnectionOvd rc = null;

			server = (Element)ns.item(i);
			NodeList appsList = server.getElementsByTagName("application");
			if (appsList.getLength() == 0) {
				Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, "Bad XML: err 3");
				return false;
			}
			Element appItem = null;

			byte flags = 0x00;
			if (this.sessionMode.equalsIgnoreCase(SESSION_MODE_DESKTOP))
				flags |= RdpConnectionOvd.MODE_DESKTOP;
			else if (this.sessionMode.equalsIgnoreCase(SESSION_MODE_REMOTEAPPS))
				flags |= RdpConnectionOvd.MODE_APPLICATION;
			if (this.multimedia.equals("1"))
				flags |= RdpConnectionOvd.MODE_MULTIMEDIA;
			if (this.printers.equals("1"))
				flags |= RdpConnectionOvd.MOUNT_PRINTERS;
			
			try {
				rc = new RdpConnectionOvd(flags);
			} catch (RdesktopException ex) {
				Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, ex.getMessage());
				continue;
			}
			
			try {
				rc.initSecondaryChannels();
			} catch (RdesktopException e1) {
				Logger.getLogger(SessionManagerCommunication.class.getName()).log(Level.SEVERE, e1.getMessage());
			}

			rc.setServer(server.getAttribute("fqdn"));
			rc.setCredentials(server.getAttribute("login"), server.getAttribute("password"));
			
			// Ensure that width is multiple of 4
			// Prevent artifact on screen with a with resolution
			// not divisible by 4
			rc.setGraphic(((int)screenSize.width & ~3), (int)screenSize.height, RdpConnectionOvd.DEFAULT_BPP);

			for (int j = 0; j < appsList.getLength(); j++) {
				appItem = (Element)appsList.item(j);
				NodeList mimeList = appItem.getElementsByTagName("mime");
				ArrayList<String> mimeTypes = new ArrayList<String>();

				if (mimeList.getLength() > 0) {
					Element mimeItem = null;
					for (int k = 0; k < mimeList.getLength(); k++) {
						mimeItem = (Element)mimeList.item(k);
						mimeTypes.add(mimeItem.getAttribute("type"));
					}
				}

				Application app = null;
				try {
					String iconWebservice = "http://"+this.sm+":1111/icon.php?id="+appItem.getAttribute("id");
					app = new Application(rc, Integer.parseInt(appItem.getAttribute("id")), appItem.getAttribute("name"), appItem.getAttribute("command"), mimeTypes, new URL(iconWebservice));
				} catch (NumberFormatException e) {
					e.printStackTrace();
					return false;
				} catch (MalformedURLException e) {
					e.printStackTrace();
					return false;
				}
				if (app != null)
					rc.addApp(app);
			}

			this.connections.add(rc);
		}
		return true;
	}

	public ArrayList<RdpConnectionOvd> getConnections() {
		return this.connections;
	}
}
