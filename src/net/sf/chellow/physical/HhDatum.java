/*
 
 Copyright 2005-2008 Meniscus Systems Ltd
 
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

import java.util.ArrayList;
import java.util.Calendar;
import java.util.Date;
import java.util.Iterator;
import java.util.List;

import net.sf.chellow.hhimport.HhDatumRaw;
import net.sf.chellow.monad.Hiber;
import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.InternalException;
import net.sf.chellow.monad.NotFoundException;
import net.sf.chellow.monad.Urlable;
import net.sf.chellow.monad.UserException;
import net.sf.chellow.monad.types.MonadUri;
import net.sf.chellow.monad.types.UriPathElement;

import org.w3c.dom.Document;
import org.w3c.dom.Element;

public class HhDatum extends PersistentEntity {
	public static final Character ACTUAL = 'A';
	public static final Character ESTIMATE = 'E';

	/*
	 * static private String getCsvField(String fieldName, String[] values, int
	 * index) throws HttpException { if (index > values.length - 1) { throw new
	 * UserException("Another field called " + fieldName + " needs to be added
	 * on to " + values); } return values[index]; }
	 */
	static private void handleException(List<String> messages, String message)
			throws HttpException {
		if (messages == null) {
			throw new UserException(message);
		} else {
			messages.add(message);
		}
	}

	static public void insert(Iterator<HhDatumRaw> rawData, List<Boolean> halt,
			List<String> messages) throws HttpException {
		if (!rawData.hasNext()) {
			return;
		}
		Calendar cal = HhEndDate.getCalendar();
		HhDatumRaw datum = rawData.next();
		String mpanCoreStr = datum.getMpanCore();
		MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr);
		SupplyGeneration generation = mpanCore.getSupply().getGeneration(
				datum.getEndDate());
		long previousDate = datum.getEndDate().getDate().getTime();
		boolean isImport = datum.getIsImport();
		boolean isKwh = datum.getIsKwh();
		if (generation == null) {
			handleException(messages, "HH datum has been ignored: "
					+ datum.toString() + ".");
		}
		Channel channel = generation.getChannel(isImport, isKwh);
		if (channel == null) {
			handleException(messages, "There is no channel for the datum: "
					+ datum.toString() + ".");
		}
		HhEndDate genFinishDate = generation.getFinishDate();
		List<HhDatumRaw> data = new ArrayList<HhDatumRaw>();
		data.add(datum);
		// HhDatumRaw firstDatum = datum;
		if (!rawData.hasNext()) {
			// batchSize = data.size();
			try {
				channel.addHhData(data);
			} catch (UserException e) {
				handleException(messages, e.getMessage());
			}
		}
		while (rawData.hasNext() && !halt.get(0)) {
			datum = rawData.next();
			Date endDate = datum.getEndDate().getDate();
			if (data.size() > 1000
					|| !(mpanCoreStr.equals(datum.getMpanCore())
							&& datum.getIsImport() == isImport
							&& datum.getIsKwh() == isKwh && endDate.getTime() == HhEndDate
							.getNext(cal, previousDate))
					|| (genFinishDate != null && genFinishDate.getDate()
							.before(endDate))) {
				// batchSize = data.size();
				try {
					channel.addHhData(data);
				} catch (UserException e) {
					handleException(messages, e.getMessage());
				}
				Hiber.close();
				data.clear();
				mpanCoreStr = datum.getMpanCore();
				mpanCore = MpanCore.getMpanCore(mpanCoreStr);
				generation = mpanCore.getSupply().getGeneration(
						datum.getEndDate());
				if (generation == null) {
					handleException(messages, "HH datum has been ignored: "
							+ datum.toString() + ".");
				}
				isImport = datum.getIsImport();
				isKwh = datum.getIsKwh();
				channel = generation.getChannel(isImport, isKwh);
				if (channel == null) {
					handleException(messages,
							"There is no channel for the datum: "
									+ datum.toString() + ".");
				}
				genFinishDate = generation.getFinishDate();
			}
			data.add(datum);
			previousDate = endDate.getTime();
		}
		if (!data.isEmpty()) {
			channel.addHhData(data);
		}
		// Hiber.close();
	}

	/*
	 * static public HhDatumRaw generalImportRaw(String[] values) throws
	 * HttpException { String mpanCoreStr = getCsvField("MPAN Core", values, 2);
	 * String date = getCsvField("Date", values, 3); String isImport =
	 * getCsvField("Is Import?", values, 4); String isKwh = getCsvField("Is
	 * Kwh?", values, 5); String value = getCsvField("Value", values, 6); String
	 * status = getCsvField("Status", values, 7); return new
	 * HhDatumRaw(mpanCoreStr, isImport, isKwh, date, value, status); }
	 */

	/*
	 * static public void generalImport(String action, String[] values) throws
	 * HttpException { String mpanCoreStr = getCsvField("MPAN Core", values, 2);
	 * MpanCore mpanCore = MpanCore.getMpanCore(mpanCoreStr); String dateStr =
	 * getCsvField("Date", values, 3); HhEndDate date = new HhEndDate(dateStr);
	 * Supply supply = mpanCore.getSupply(); SupplyGeneration supplyGeneration =
	 * supply.getGeneration(date); String isImportStr = getCsvField("Is
	 * Import?", values, 4); boolean isImport =
	 * Boolean.parseBoolean(isImportStr); String isKwhStr = getCsvField("Is
	 * Kwh?", values, 5); boolean isKwh = Boolean.parseBoolean(isKwhStr);
	 * Channel channel = supplyGeneration.getChannel(isImport, isKwh); if
	 * (action.equals("insert")) { String valueStr = getCsvField("Value",
	 * values, 6); float value = Float.parseFloat(valueStr); String statusStr =
	 * getCsvField("Status", values, 7); HhDatumRaw datumRaw = new
	 * HhDatumRaw(mpanCoreStr, isImport, isKwh, date, value, status); List<HhDatumRaw>
	 * dataRaw = new ArrayList<HhDatumRaw>(); dataRaw.add(datumRaw);
	 * channel.addHhData(supplyGeneration.getHhdcContract(), dataRaw); } }
	 */
	private Channel channel;

	private HhEndDate endDate;

	private float value;

	private Character status;

	public HhDatum() {
	}

	public HhDatum(Channel channel, HhDatumRaw datumRaw) throws HttpException {
		setChannel(channel);
		HhEndDate endDate = datumRaw.getEndDate();
		if (endDate == null) {
			throw new InternalException("The value 'endDate' must not be null.");
		}
		setEndDate(endDate);
		update(datumRaw.getValue(), datumRaw.getStatus());
	}

	public Channel getChannel() {
		return channel;
	}

	void setChannel(Channel channel) {
		this.channel = channel;
	}

	public HhEndDate getEndDate() {
		return endDate;
	}

	void setEndDate(HhEndDate endDate) {
		this.endDate = endDate;
	}

	public float getValue() {
		return value;
	}

	void setValue(float value) {
		this.value = value;
	}

	public Character getStatus() {
		return status;
	}

	void setStatus(Character status) {
		this.status = status;
	}

	public void update(float value, Character status) throws HttpException {
		this.value = value;
		if (status != null
				&& !(status.equals(ESTIMATE) || status.equals(ACTUAL))) {
			throw new UserException(
					"The status character must be E, A or null.");
		}
		this.status = status;
	}

	public Element toXml(Document doc) throws HttpException {
		Element element = super.toXml(doc, "hh-datum");

		element.appendChild(endDate.toXml(doc));
		element.setAttribute("value", Float.toString(value));
		if (status != null) {
			element.setAttribute("status", Character.toString(status));
		}
		return element;
	}

	public String toString() {
		return "End date " + endDate + ", Value " + value + ", Status "
				+ status;
	}

	public MonadUri getUri() throws HttpException {
		return channel.getHhDataInstance().getUri().resolve(getUriId());
	}

	public Urlable getChild(UriPathElement urlId) throws HttpException {
		throw new NotFoundException();
	}
}
