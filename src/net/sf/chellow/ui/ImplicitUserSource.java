/*******************************************************************************
 * 
 *  Copyright (c) 2005, 2012 Wessex Water Services Limited
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
package net.sf.chellow.ui;

import net.sf.chellow.monad.HttpException;
import net.sf.chellow.monad.Invocation;
import net.sf.chellow.monad.types.EmailAddress;
import net.sf.chellow.physical.Configuration;
import net.sf.chellow.physical.User;

public class ImplicitUserSource {
	static public User getUser(Invocation inv) throws HttpException {
		User user = null;
		Configuration configuration = Configuration.getConfiguration();
		String emailAddressString = configuration.getProperty("ip*-*-*-*");

		if (emailAddressString == null) {
			emailAddressString = configuration.getProperty("ip"
					+ inv.getRequest().getRemoteAddr().replace(".", "-"));
		}
		if (emailAddressString != null) {
			user = User.findUserByEmail(new EmailAddress(emailAddressString
					.trim()));
		}
		return user;
	}
}
