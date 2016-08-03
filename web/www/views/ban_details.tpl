<html>

<head>
  <title>Ban Details</title>
  <link href="/static/vbaner.css" rel="stylesheet" type="text/css" />
  <meta http-equiv="refresh" content="5" />
</head>

<body>
% include('header.tpl', title='Ban Details')

<div class='center'>
<table>
  <tr><td>ID</td><td>{{ban['_id']}}</td></tr>
  <tr><td>Submission Date</td><td>{{ban['createdAt']}}</td></tr>
  <tr><td>Extended Status</td><td>
%    for srv in ban['extendedStatus']:
%       if ban['extendedStatus'][srv] == 'OK':
<span>{{srv}}/</span><img src="/static/green.png" alt="{{srv}}" title="{{srv}}" />
%       elif ban['extendedStatus'][srv] == 'PENDING':
<span>{{srv}}/</span><img src="/static/blue.png" alt="{{srv}}" title="{{srv}}" />
%       else:
<span>{{srv}}/</span><img src="/static/red.png" alt="{{srv}}" title="{{srv}}" />
%       end
%    end
  </td></tr> 

  <tr><td>Origin</td><td>{{ban['origin']}}</td></tr>
  <tr><td>Parameters</td><td>
%    for i in sorted(ban['parameters']):
  <p>{{i}}: {{ban['parameters'][i]}}</p>
%    end    

  </td></tr> 
  <tr><td>Priority</td><td>{{ban['priority']}}</td></tr>
  <tr><td>Status</td><td>{{ban['status']}}</td></tr>
  <tr><td>Tries</td><td>{{ban['tries']}}</td></tr>
</table>
</div>
</body>
</html>
