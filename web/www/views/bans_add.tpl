<html>

<head>
  <title>Submit Ban</title>
  <link href="/static/vbaner.css" rel="stylesheet" type="text/css" />
</head>

<body>
% include('header.tpl', title='Submit Bans')

<div class='center'>

<div style="margin: 0 auto; width: 300px;">
<form action="/ban/submit" method="post" style="width: 50%;">
 <table id='foo'>
 <tr><td>CompanyId</td><td><input name="companyId"></td></tr>
 <tr><td>Site</td><td>
 <select name='site'>
   <option value="" disabled="disabled" selected="selected" style="display: none;">select a site</option>
   <option value="directindustry">directindustry</option>
   <option value="archiexpo">archiexpo</option>
   <option value="nauticexpo">nauticexpo</option>
   <option value="medicalexpo">medicalexpo</option>
 </select></td></tr>
 <tr><td></td><td><button>Submit</button></td></tr>
 </table>
</form>
</div>


</div>
</body>
</html>
