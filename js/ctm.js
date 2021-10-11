//$notification.post("req", "",$response.body);
if($response.body.indexOf('"acctAmount":"0.0"') != -1){
    $body = $response.body.replace('"acctAmount":"0.0"', '"acctAmount":"10.3"');
    //$notification.post("Replaced body", "",$response.body);
    $done({status: 200, headers: $response.headers, body: $body })
}else{
    $done({})
}
