<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/">
    <html>
      <head>
        <title> Log <xsl:value-of select="Log/@id" /></title>
      </head>
      <body>

  <TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
  <COL width="33%"/>
  <COL width="33%"/>
  <COL width="33%"/>
  <TR bgcolor="Gray">
  <TH>Test case</TH>
  <TH>Result</TH>
  <TH>Time</TH>
  </TR>
  <TR>
  <TD><xsl:value-of select="Log/@id"/></TD>
  <TD><xsl:value-of select="Log/TestCaseResult"/></TD>
  <TD><xsl:value-of select="Log/@time"/></TD>
  </TR>
 </TABLE> 

  <hr/>
  <h3> Detailed Log </h3>
  <hr/>

  <TABLE cellpadding="4" style="border: 0px solid #000000; border-collapse: collapse;" border="1">
	<xsl:for-each select="Log/LogItem">

	 <TR>
	  <TD><xsl:value-of select="DateTime"/></TD>
	  
	  <TD> <xsl:value-of select="CommandGroup/Source/Name"/> --> </TD>

	  <TD> <xsl:value-of select="CommandGroup/Destination/Name"/></TD>
	  <TD><xsl:value-of select="CommandGroup/Command"/></TD>
	 </TR>
	</xsl:for-each>

   </TABLE>

    </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
