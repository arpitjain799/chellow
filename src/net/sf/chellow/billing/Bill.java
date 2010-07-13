/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2009 Wessex Water Services Limited
 *  
 *  This file is part of Chellow.
 * 
 *  Chellow is free software: you can redistribute it and/or modify
 *  it under the terms of the GNU General Public License as published by
 *  the Free Software Foundation, either version 3 of the License, or
 *  (at your option) any later version.
 * 
 *  Chellow is distributed in the hope that it will be useful,
 *  but WITHOUT ANY WARRANTY; without even the implied warranty of
 *  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 *  GNU General Public License for more details.
 * 
 *  You should have received a copy of the GNU General Public License
 *  along with Chellow.  If not, see <http://www.gnu.org/licenses/>.
 *  
 *******************************************************************************/

package net.sf.chellow.billing;

import java.math.BigDecimal;
import java.util.Date;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.MonadUtils;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.XmlTree;
import net.sf.chellow.monad.types.MonadDate;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;
import net.sf.chellow.physical.HhStartDate;
import net.sf.chellow.physical.PersistentEntity;
import net.sf.chellow.physical.RawRegisterRead;
import net.sf.chellow.physical.RegisterRead;
import net.sf.chellow.physical.RegisterReads;
import net.sf.chellow.physical.Supply;
import net.sf.chellow.physical.SupplySnag;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class Bill extends PersistentEntity implements Urlable {
	public static Bill getBill(Long id) throws HttpException {
		Bill bill = (Bill) Hiber.session().get(Bill.class, id);
		if (bill == null) {
			throw new UserException("There isn't a bill with that id.");
		}
		return bill;
	}

	private Batch batch;

	private Supply supply;

	private Date issueDate;

	private HhStartDate startDate;

	private HhStartDate finishDate;

	private BigDecimal net;

	private BigDecimal vat;

	private String reference;

	private Boolean isPaid; // Null is pending, false is rejected.

	private String type;

	private String breakdown;

	private BigDecimal kwh;

	private boolean isCancelledOut;

	private Set<RegisterRead> reads;

	public Bill() {
	}

	public Bill(Batch batch, Supply supply) throws HttpException {
		setBatch(batch);
		setSupply(supply);
		setReference("Default Reference");
		setType("");
		setBreakdown("");
		setKwh(new BigDecimal(0));
		setNet(new BigDecimal(0));
		setVat(new BigDecimal(0));
		setStartDate(HhStartDate.roundDown(new Date()));
		setFinishDate(HhStartDate.roundDown(new Date()));
		setIsCancelledOut(false);
	}

	public Batch getBatch() {
		return batch;
	}

	public void setBatch(Batch batch) {
		this.batch = batch;
	}

	public Supply getSupply() {
		return supply;
	}

	public void setSupply(Supply supply) {
		this.supply = supply;
	}

	public Date getIssueDate() {
		return issueDate;
	}

	protected void setIssueDate(Date issueDate) {
		this.issueDate = issueDate;
	}

	public HhStartDate getStartDate() {
		return startDate;
	}

	protected void setStartDate(HhStartDate startDate) {
		this.startDate = startDate;
	}

	public HhStartDate getFinishDate() {
		return finishDate;
	}

	protected void setFinishDate(HhStartDate finishDate) {
		this.finishDate = finishDate;
	}

	public BigDecimal getNet() {
		return net;
	}

	void setNet(BigDecimal net) {
		this.net = net;
	}

	public BigDecimal getVat() {
		return vat;
	}

	void setVat(BigDecimal vat) {
		this.vat = vat;
	}

	public String getReference() {
		return reference;
	}

	public void setReference(String reference) {
		this.reference = reference;
	}

	public Boolean getIsPaid() {
		return isPaid;
	}

	public void setIsPaid(Boolean isPaid) {
		this.isPaid = isPaid;
	}

	public String getType() {
		return type;
	}

	public void setType(String type) {
		this.type = type;
	}

	public String getBreakdown() {
		return breakdown;
	}

	public void setBreakdown(String breakdown) {
		this.breakdown = breakdown;
	}

	public boolean getIsCancelledOut() {
		return isCancelledOut;
	}

	public void setIsCancelledOut(boolean isCancelledOut) {
		this.isCancelledOut = isCancelledOut;
	}

	void setKwh(BigDecimal kwh) {
		this.kwh = kwh;
	}

	public BigDecimal getKwh() {
		return kwh;
	}

	void setReads(Set<RegisterRead> reads) {
		this.reads = reads;
	}

	public Set<RegisterRead> getReads() {
		return reads;
	}

	public void update(String reference, Date issueDate, HhStartDate startDate,
			HhStartDate finishDate, BigDecimal kwh, BigDecimal net,
			BigDecimal vat, String type, Boolean isPaid,
			boolean isCancelledOut, String breakdown) throws HttpException {
		setReference(reference);
		setIssueDate(issueDate);
		if (startDate.getDate().after(finishDate.getDate())) {
			throw new UserException(
					"The bill start date can't be after the finish date.");
		}
		setStartDate(startDate);
		setFinishDate(finishDate);
		if (kwh == null) {
			throw new InternalException("kwh can't be null.");
		}
		setKwh(kwh);
		setNet(net);
		setVat(vat);
		if (type == null) {
			throw new InternalException("Type can't be null.");
		}
		setType(type);
		setIsPaid(isPaid);
		setIsCancelledOut(isCancelledOut);
		setBreakdown(breakdown);
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "bill");
		element.appendChild(new MonadDate("issue", issueDate).toXml(doc));
		startDate.setLabel("start");
		element.appendChild(startDate.toXml(doc));
		finishDate.setLabel("finish");
		element.appendChild(finishDate.toXml(doc));
		element.setAttribute("kwh", kwh.toString());
		element.setAttribute("net", net.toString());
		element.setAttribute("vat", vat.toString());
		element.setAttribute("reference", reference);
		if (isPaid != null) {
			element.setAttribute("is-paid", Boolean.toString(isPaid));
		}
		element.setAttribute("is-cancelled-out", Boolean
				.toString(isCancelledOut));
		element.setAttribute("type", type);
		element.setAttribute("breakdown", breakdown);
		return element;
	}

	public void httpPost(Invocation inv) throws HttpException {
		if (inv.hasParameter("delete")) {
			delete();
			Hiber.commit();
			inv.sendSeeOther(batch.billsInstance().getUri());
		} else {
			String reference = inv.getString("reference");
			Date issueDate = inv.getDate("issue-date");
			Date startDate = inv.getDate("start");
			Date finishDate = inv.getDate("finish");
			BigDecimal kwh = inv.getBigDecimal("kwh");
			BigDecimal net = inv.getBigDecimal("net");
			BigDecimal vat = inv.getBigDecimal("vat");
			String type = inv.getString("type");
			Boolean isPaid = inv.getBoolean("isPaid");
			Boolean isCancelledOut = inv.getBoolean("isCancelledOut");
			String breakdown = inv.getString("breakdown");

			if (!inv.isValid()) {
				throw new UserException(document());
			}
			update(reference, issueDate, new HhStartDate(startDate).getNext(),
					new HhStartDate(finishDate), kwh, net, vat, type, isPaid,
					isCancelledOut, breakdown);
			Hiber.commit();
			inv.sendOk(document());
		}
	}

	private Document document() throws HttpException {
		Document doc = MonadUtils.newSourceDocument();
		Element source = doc.getDocumentElement();
		Element billElement = (Element) toXml(doc, new XmlTree("batch",
				new XmlTree("contract", new XmlTree("party"))).put("reads")
				.put("supply"));
		source.appendChild(billElement);
		source.appendChild(MonadDate.getMonthsXml(doc));
		source.appendChild(MonadDate.getDaysXml(doc));
		return doc;
	}

	public void httpGet(Invocation inv) throws HttpException {
		inv.sendOk(document());
	}

	public MonadUri getUri() throws HttpException {
		return batch.billsInstance().getUri().resolve(getUriId()).append("/");
	}

	public Urlable getChild(UriPathElement uriId) throws HttpException {
		if (RegisterReads.URI_ID.equals(uriId)) {
			return registerReadsInstance();
		} else {
			throw new NotFoundException();
		}
	}

	public RegisterReads registerReadsInstance() {
		return new RegisterReads(this);
	}

	public RegisterRead insertRead(RawRegisterRead rawRead)
			throws HttpException {
		RegisterRead read = new RegisterRead(this, rawRead);
		if (reads == null) {
			reads = new HashSet<RegisterRead>();
		}
		reads.add(read);
		Hiber.flush();
		read.attach();
		return read;
	}

	@SuppressWarnings("unchecked")
	public void delete() throws HttpException {
		Hiber.session().delete(this);
		Hiber.flush();
		HhStartDate snagStart = startDate;
		if (!isCancelledOut) {
			for (Bill bill : (List<Bill>) Hiber
					.session()
					.createQuery(
							"from Bill bill where bill.batch.contract.id = :contractId and bill.supply = :supply and bill.isCancelledOut is false and bill.startDate.date <= :finishDate and bill.finishDate.date >= :startDate order by bill.startDate.date")
					.setLong("contractId", batch.getContract().getId())
					.setEntity("supply", getSupply()).setTimestamp("startDate",
							startDate.getDate()).setTimestamp("finishDate",
							finishDate.getDate()).list()) {
				if (bill.getStartDate().after(snagStart)) {
					supply.addSnag(batch.getContract(),
							SupplySnag.MISSING_BILL, snagStart, bill
									.getStartDate().getPrevious());
					snagStart = bill.getFinishDate().getNext();
				}
			}
			if (!snagStart.after(finishDate)) {
				supply.addSnag(batch.getContract(), SupplySnag.MISSING_BILL,
						snagStart, finishDate);
			}
		}
		Hiber.flush();
	}
}