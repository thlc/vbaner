<html>

<head>
  <title>AutoBans</title>
  <link href="/static/vbaner.css" rel="stylesheet" type="text/css" />
</head>

<body>
% include('header.tpl', title='Bans')

<div class='center'>

<span>Number of items to show:</span>
<form action = "/bans/view" method = "GET">

  <select name = "items">
      <option value = "100">100</option>
      <option value = "500">500</option>
      <option value = "1000">1000</option>
  </select>

  <input type = "submit" />

</form>

<table class='pretty'>
    <tr>
      <th>ID</th>
      <th>Submission date</th>
      <th>Tries</th>
      <th>ExtStatus</th>
      <th>Status</th>
      <th><i>CompanyID</i></th>
      <th><i>Site</i></th>
    </tr>
%  for ban in ban_list.limit(int(items)):
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
%    if ban['status'] == 'completed' or ban['status'] == 'processing':
%      color = '#c6ffdb'
%    elif ban['status']  == 'full-fail':
%      color = '#ff5353'
%    elif ban['status'] == 'partial-fail':
%      color = '#ffbc53'
%    elif ban['status'] == 'pending':
%      color = '#a7baff'
%    else:
%      color = '#eeeeee'
%    end
      <td style="background: {{color}}">{{ban['status']}}</td>
      <td>
%    if 'companyId' in ban['parameters']:
{{ban['parameters']['companyId']}}
%    end
      </td>
      <td>
%    if 'site' in ban['parameters']:
{{ban['parameters']['site']}}
%     end
      </td>
    </tr>
%  end
</table>
</div>
</body>
</html>
