const testConfig = `[common]
server_addr = "bj-1.muhanfrp.cn"
serverPort = "7000"

[[proxies]]
name = "test-tcp"
type = "tcp"
localIP = "127.0.0.1"
localPort = "22"
remotePort = '6000'


[4BSC3rdY98jQ13h6HK]
type = tcp
local_ip = 127.0.0.1
local_port = 80
remote_port = 11988

[HmKFbCB9jRJyWwZvEs]
type = tcp
local_ip = 127.0.0.1
local_port = 80
remote_port = '33257"

[TTM9xzedLxk82Ouocm]
type = http
local_ip = 127.0.0.1
local_port = 90
custom_domains = nmb.cn

[ftkMxHiqmUkcj1Bwd7]
type = https
local_ip = 127.0.0.1
local_port = 90
custom_domains = 45.nmb.cn
`;

const accessLinks = extractAccessLinks(testConfig);
console.log(accessLinks);

