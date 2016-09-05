<html>

<head>
  <title>Submit Ban</title>
  <link href="/static/vbaner.css" rel="stylesheet" type="text/css" />
</head>

<body>
% include('header.tpl', title='Submit Bans')

<div class='center'>

<div style="margin: 0 auto; width: 400px;">

<h3>HTML</h3>
<form action="/ban/submit" method="post" style="width: 50%;">
  <input type="hidden" name="target" value="html">
  <table id='foo'>
    <tr><td>CompanyId</td><td><input name="companyId"></td></tr>
    <tr><td>MatchRule ID</td><td>
      <select name="matchRule">
	<option value="">choose a MR</option>
	<option value="1">1 - foo</option>
	<option value="2">2 - bar</option>
	<option value="3">3 - baz</option>
	<option value="4">4 - ...</option>
      </select>
    </td></tr>
    <tr><td>Site</td><td>
      <select name='site'>
	<option value="" selected="selected">(all sites)</option>
	<option value="directindustry">directindustry</option>
	<option value="archiexpo">archiexpo</option>
	<option value="nauticexpo">nauticexpo</option>
	<option value="medicalexpo">medicalexpo</option>
      </select>
    </td></tr>
    <tr>
      <td>vsClientId</td>
      <td><input name="vsClientId"></td>
    </tr>
    <tr><td></td><td><button>Submit</button></td></tr>
  </table>
</form>

<h3>Static</h3>
<form action="/ban/submit" method="post" style="width: 50%;">
  <input type="hidden" name="target" value="static">
  <table id="foo">
    <tr>
      <td>URL</td>
      <td><input name="url"></td>
    </tr>
    <tr>
      <td>Subdomain</td>
      <td><input name="subdomain"></td>
    </tr>
    <tr><td></td><td><button>Submit</button></td></tr>
  </table>
</form>
 
</div>

</div>
</body>
</html>
