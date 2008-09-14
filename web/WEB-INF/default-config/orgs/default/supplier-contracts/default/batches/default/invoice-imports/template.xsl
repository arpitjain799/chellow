<?xml version="1.0" encoding="us-ascii"?>
<xsl:stylesheet version="1.0"
	xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
	<xsl:output method="html" encoding="US-ASCII"
		doctype-public="-//W3C//DTD HTML 4.01//EN"
		doctype-system="http://www.w3.org/TR/html4/strict.dtd" indent="yes" />
	<xsl:template match="/">
		<html>
			<head>
				<link rel="stylesheet" type="text/css"
					href="{/source/request/@context-path}/style/" />

				<title>
					Chellow &gt; Organizations &gt;
					<xsl:value-of
						select="/source/invoice-imports/batch/supplier-contract/org/@name" />
					&gt; Supplier Contracts &gt;
					<xsl:value-of
						select="/source/invoice-imports/batch/supplier-contract/@name" />
					&gt; Batches &gt;
					<xsl:value-of
						select="/source/invoice-imports/batch/@name" />
					&gt; Invoice Imports
				</title>
			</head>

			<body>
				<p>
					<a href="{/source/request/@context-path}/">
						<img
							src="{/source/request/@context-path}/logo/" />
						<span class="logo">Chellow</span>
					</a>
					&gt;
					<a href="{/source/request/@context-path}/orgs/">
						<xsl:value-of select="'Organizations'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-imports/batch/supplier-contract/org/@id}/">
						<xsl:value-of
							select="/source/invoice-imports/batch/supplier-contract/org/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-imports/batch/supplier-contract/org/@id}/supplier-contracts/">
						<xsl:value-of select="'Supplier Contracts'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-imports/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-imports/batch/supplier-contract/@id}/">
						<xsl:value-of
							select="/source/invoice-imports/batch/supplier-contract/@name" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-imports/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-imports/batch/supplier-contract/@id}/batches/">
						<xsl:value-of select="'Batches'" />
					</a>
					&gt;
					<a
						href="{/source/request/@context-path}/orgs/{/source/invoice-imports/batch/supplier-contract/org/@id}/supplier-contracts/{/source/invoice-imports/batch/supplier-contract/@id}/batches/{/source/invoice-imports/batch/@id}/">
						<xsl:value-of
							select="/source/invoice-imports/batch/@reference" />
					</a>
					&gt;
					<xsl:value-of select="'Invoice Imports'" />
				</p>
				<xsl:if test="/source/message">
					<ul>
						<xsl:for-each select="/source/message">
							<li>
								<xsl:value-of select="@description" />
							</li>
						</xsl:for-each>
					</ul>
				</xsl:if>
				<br />
				<xsl:choose>
					<xsl:when
						test="/source/response/@status-code = '201'">
						<p>
							The
							<a
								href="{/source/response/header[@name = 'Location']/@value}">
								<xsl:value-of
									select="'new invoice import'" />
							</a>
							has been successfully created.
						</p>
					</xsl:when>
					<xsl:otherwise>
						<ul>
							<xsl:for-each
								select="/source/invoice-imports/invoice-import">
								<li>
									<a href="{@id}/">
										<xsl:value-of select="@id" />
									</a>
								</li>
							</xsl:for-each>
						</ul>
						<form enctype="multipart/form-data" action="."
							method="post">
							<fieldset>
								<legend>Import invoices</legend>
								<br />
								<label>
									<a
										href="http://chellow.wikispaces.com/ImportingInvoices">
										<xsl:value-of select="'File'" />
									</a>
									<xsl:value-of select="' '" />
									<input type="file" name="file"
										value="{/source/request/parameter[@name = 'file']/value}" />
								</label>
								<br />
								<br />
								<input type="submit" value="Import" />
								<input type="reset" value="Reset" />
							</fieldset>
						</form>
					</xsl:otherwise>
				</xsl:choose>
			</body>
		</html>
	</xsl:template>
</xsl:stylesheet>