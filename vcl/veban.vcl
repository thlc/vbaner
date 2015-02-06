# 1. VEBAN method
sub vcl_recv {
  if (req.request == "VEBAN") {
    if (!client.ip ~ purge) {
      error 501 "Method Not Implemented";
    }
    if (req.http.X-VE-BanKey != "complex-stuff-here") {
      error 403 "Forbidden";
    }
    if (!req.http.X-VE-BanStr) {
      error 911 "Bad VEBAN request (missing X-VE-BanStr)";
    }
    ban(req.http.X-VE-BanStr);
    std.log("VEBAN added ban [" + req.http.X-VE-BanStr + "]");
    error 910 "VEBAN OK";
  }
}
