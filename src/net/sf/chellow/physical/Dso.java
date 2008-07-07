/*
 
 Copyright 2005, 2008 Meniscus Systems Ltd
 
 This file is part of Chellow.

 Chellow is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 2 of the License, or
 (at your option) any later version.

 Chellow is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with Chellow; if not, write to the Free Software
 Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

 */

package net.sf.chellow.physical;

import java.util.Date;

import net.sf.chellow.billing.DsoService;
import net.sf.chellow.billing.DsoServices;
import net.sf.chellow.billing.Provider;
import net.sf.chellow.monad.DesignerException;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.ui.Chellow;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Dso extends Provider {
	static public Dso getDso(DsoCode code) throws InternalException,
			HttpException {
		Dso dso = findDso(code.getString());
		if (dso == null) {
			throw new UserException("There is no DSO with the code '" + code
					+ "'.");
		}
		return dso;
	}

	static public Dso findDso(String code) throws InternalException,
			HttpException {
		return (Dso) Hiber.session().createQuery(
				"from Dso as dso where dso.code.string = :code").setString(
				"code", code).uniqueResult();
	}

	static public Dso getDso(Long id) throws InternalException, HttpException {
		Dso dso = (Dso) Hiber.session().get(Dso.class, id);
		if (dso == null) {
			throw new UserException("There isn't a DSO with that id.");
		}
		return dso;
	}

	static public Dso getDso(String participantCode) throws HttpException {
		Dso dso = (Dso) Hiber.session().createQuery(
				"from Dso dso where dso.participant.code = :participantCode")
				.setString("participantCode", participantCode).uniqueResult();
		if (dso == null) {
			throw new NotFoundException();
		}
		return dso;
	}

	/*
	 * public static Dso insertDso() throws HttpException {
	 * 
	 * Dso dso = null; try { dso = new Dso(name, code);
	 * Hiber.session().save(dso); Hiber.flush(); } catch (HibernateException e) {
	 * if (Data .isSQLException(e, "ERROR: duplicate key violates unique
	 * constraint \"site_code_key\"")) { throw new UserException ("A site with
	 * this code already exists."); } else { throw new InternalException(e); } }
	 * return dso; }
	 */
	private DsoCode code;

	public Dso() {
	}

	public Dso(String name, Participant participant, Date from, Date to,
			DsoCode code) throws HttpException {
		super(name, participant, MarketRole.DISTRIBUTOR, from, to);
		setCode(code);
	}

	void setCode(DsoCode code) {
		this.code = code;
	}

	public DsoCode getCode() {
		return code;
	}

	public boolean isSettlement() {
		return Integer.parseInt(code.toString()) < 24;
	}

	public Llfc getLlfc(LlfcCode code) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validTo is null")
				.setEntity("dso", this).setInteger("code", code.getInteger())
				.uniqueResult();
		if (llfc == null) {
			throw new UserException("There is no ongoing LLFC with the code "
					+ code + " associated with this DNO.");
		}
		return llfc;
	}

	public Llfc getLlfc(LlfcCode code, Date date) throws HttpException {
		Llfc llfc = (Llfc) Hiber
				.session()
				.createQuery(
						"from Llfc llfc where llfc.dso = :dso and llfc.code = :code and llfc.validFrom <= :date and (llfc.validTo is null or llfc.validTo >= :date)")
				.setEntity("dso", this).setInteger("code", code.getInteger())
				.setTimestamp("date", date).uniqueResult();
		if (llfc == null) {
			throw new UserException(
					"There is no line loss factor with the code " + code
							+ " associated with the DNO '"
							+ getCode().toString() + "' for the date "
							+ date.toString() + ".");
		}
		return llfc;
	}

	public String toString() {
		return "Code: " + code + " Name: " + getName();
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = (Element) super.toXml(doc);
		element.setAttribute("code", code.toString());
		return element;
	}

	public MonadUri getUri() throws InternalException, HttpException {
		return Chellow.PROVIDERS_INSTANCE.getUri().resolve(getUriId()).append(
				"/");
	}

	public void httpGet(Invocation inv) throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		source.appendChild(toXml(doc));
		inv.sendOk(doc);
	}

	public void httpPost(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (DsoServices.URI_ID.equals(uriId)) {
			return new DsoServices(this);
		} else if (Llfcs.URI_ID.equals(uriId)) {
			return new Llfcs(this);
		} else if (MpanTops.URI_ID.equals(uriId)) {
			return new MpanTops(this);
		} else {
			throw new NotFoundException();
		}
	}

	public void httpDelete(Invocation inv) throws InternalException,
			HttpException {
		// TODO Auto-generated method stub

	}

	/*
	 * @Override public List<SupplyGeneration> supplyGenerations(Account
	 * account) { // TODO Auto-generated method stub return null; }
	 */

	public DsoService insertService(String name, HhEndDate startDate,
			String chargeScript) throws HttpException, InternalException,
			DesignerException {
		DsoService service = findService(name);
		if (service == null) {
			service = new DsoService(this, name, startDate, chargeScript);
		} else {
			throw new UserException(
					"There is already a DSO service with this name.");
		}
		Hiber.session().save(service);
		Hiber.flush();
		return service;
	}

	public DsoService getService(String name) throws HttpException {
		DsoService dsoService = findService(name);
		if (dsoService == null) {
			throw new UserException("The DSO service " + name
					+ " doesn't exist.");
		}
		return dsoService;
	}

	public DsoService findService(String name) throws HttpException,
			InternalException {
		return (DsoService) Hiber
				.session()
				.createQuery(
						"from DsoService service where service.provider = :provider and service.name = :serviceName")
				.setEntity("provider", this).setString("serviceName", name)
				.uniqueResult();
	}

	public DsoServices servicesInstance() {
		return new DsoServices(this);
	}
}