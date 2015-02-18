<html>

<head>
  <title>AutoBans</title>
  <link href="/static/vbaner.css" rel="stylesheet" type="text/css" />
</head>

<body>
% include('header.tpl', title='Bans')

<div class='center'>
<table class='pretty'>
    <tr>
      <th>ID</th>
      <th>Submission date</th>
      <th>Tries</th>
      <th>ExtStatus</th>
      <th>Status</th>
    </tr>
%  for ban in ban_list:
    <tr>
      <td><a href='/ban/details/{{ban['_id']}}'><span style="font-family: monospace;">{{ban['_id']}}</span></a></td>
      <td>{{ban['createdAt']}}</td>
      <td>{{ban['tries']}}</td>
      <td>
%    for srv in ban['extendedStatus']:
%       if ban['extendedStatus'][srv] == u'OK':
<img src="/static/green.png" alt="{{srv}}" title="{{srv}}" />
%       elif ban['extendedStatus'][srv] == u'PENDING':
<img src="/static/blue.png" alt="{{srv}}" title="{{srv}}" />
%       else:
<img src="/static/red.png" alt="{{srv}}" title="{{srv}}" />
%       end
%    end
      </td>
      <td>{{ban['status']}}</td>
    </tr>
%  end
</table>
</div>
</body>
</html>
