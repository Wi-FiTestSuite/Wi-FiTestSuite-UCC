<?xml version="1.0"?>
<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version="1.0">
  <xsl:template match="/">
    <html>
      <head>
        <title> Results Summary <xsl:value-of select="Results/Result/DUT/CID"/></title>
      </head>
      <body>
       <h1>Results Summary CID - <xsl:value-of select="Results/Result/DUT/CID"/></h1>

<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
  <COL width="10%"/>
  <COL width="15%"/>
  <COL width="20%"/>
  <COL width="15%"/>
  <COL width="20%"/>
  <COL width="15%"/>
 <TR bgcolor="Gray">DUT</TR>
 <TR bgcolor="Gray">
  <TH>DUT Name</TH>
  <TH>WTS Version</TH>
  <TH>Vendor Name</TH>
  <TH>Device Model</TH>
  <TH>Device Firmware</TH>
  <TH>Supported Optional Feature</TH>
 </TR>
  <TR>
  <TD><xsl:value-of select="Results/Result/DUT/Name"/></TD>
  <TD><xsl:value-of select="Results/Result/DUT/WTSControlAgent"/></TD>
  <TD><xsl:value-of select="Results/Result/DUT/Vendor"/></TD>
  <TD><xsl:value-of select="Results/Result/DUT/Model"/></TD>
  <TD><xsl:value-of select="Results/Result/DUT/Driver"/></TD>

  <TD><xsl:value-of select="Results/Result/Versions/DUT/FeatureList"/></TD>
 </TR>
 </TABLE> <br/>

<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
  <COL width="15%"/>
  <COL width="15%"/>
  <COL width="20%"/>
  <COL width="15%"/>
  <COL width="10%"/>
  <COL width="25%"/>

 <TR bgcolor="Gray">Test Bed</TR>
 <TR bgcolor="Gray">
  <TH>WTS Version</TH>
  <TH>Vendor Name</TH>
  <TH>Device Model</TH>
  <TH>Device Firmware</TH>
  <TH>Verification</TH>
  <TH>Details</TH>
 </TR>
 <xsl:for-each select="Results/Result/Testbed/Device">
 <TR>
  <TD><xsl:value-of select="WTSControlAgent"/></TD>
  <TD><xsl:value-of select="Vendor"/></TD>
  <TD><xsl:value-of select="Model"/></TD>
  <TD><xsl:value-of select="Driver"/></TD>
  <xsl:choose>
  <xsl:when test="Verification/Status = 'OK'">
	  <TD bgcolor="Green"><xsl:value-of select="Verification/Status"/></TD>
  </xsl:when>
  <xsl:otherwise>
	  <TD bgcolor="Gray"><xsl:value-of select="Verification/Status"/></TD>
   </xsl:otherwise>
   </xsl:choose>
  <TD><xsl:value-of select="Verification/Message"/></TD>
 </TR>
</xsl:for-each>
</TABLE><br/>
<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
  <COL width="33%"/>
  <COL width="33%"/>
  <COL width="33%"/>
 <TR bgcolor="Gray">
  <TH>WTS Component Name</TH>
  <TH>WTS Version</TH>
  <TH>Other Info</TH>
 </TR>
  <xsl:for-each select="Results/Result/WTS/WTSComponent">
  <TR>
  <TD><xsl:value-of select="Name"/></TD>
  <TD><xsl:value-of select="Version"/></TD>
  <TD><xsl:value-of select="Others"/></TD>
 </TR>
</xsl:for-each>
</TABLE> <br/>
<TABLE cellpadding="4" style="border: 1px solid #000000; border-collapse: collapse;" border="1">
  <COL width="10%"/>
  <COL width="10%"/>
  <COL width="5%"/>
  <COL width="5%"/>
  <COL width="10%"/>
  <COL width="10%"/>
  <COL width="45%"/>
 <TR bgcolor="Gray">
  <TH>Test Case</TH>
  <TH>Result</TH>
  <TH>Actual</TH>
  <TH>Expected</TH>
  <TH>Stats</TH>
  <TH>Type</TH>
  <TH>Log Files</TH>
 </TR>
 <xsl:for-each select="Results/Result/TestResults/TestCase">
 <TR>
  <TD><xsl:value-of select="TestID"/></TD>

  <xsl:choose>
  <xsl:when test="contains(Result, 'PASS')">
	  <TD bgcolor="Green"><xsl:value-of select="Result"/></TD>
  </xsl:when>
  <xsl:otherwise>
	  <TD bgcolor="Red"><xsl:value-of select="Result"/></TD>
   </xsl:otherwise>

   </xsl:choose>
  <TD><xsl:value-of select="R1"/></TD>
  <TD><xsl:value-of select="R2"/></TD>
  <TD>Total Run: <b> <xsl:value-of select="Stats/TotalRun"/> <a><br/></a> <a><br/></a></b>PASS: <b><xsl:value-of select="Stats/TotalPASS"/></b><a><br/></a>FAIL: <b><xsl:value-of select="Stats/TotalFAIL"/></b><a><br/></a>INCOMPLETE: <b><xsl:value-of select="Stats/TotalERROR"/></b></TD>
  <TD><xsl:value-of select="Type"/> [<xsl:value-of select="OptionalFeature"/>]</TD>
  <TD>
       <xsl:for-each select="LogFiles/LogFile">         
        <a href="{Name}"> <xsl:value-of select="Name"/>  <br/> </a> 
       </xsl:for-each>

  </TD>
 </TR>
</xsl:for-each>
</TABLE>
    </body>
    </html>
  </xsl:template>
</xsl:stylesheet>
