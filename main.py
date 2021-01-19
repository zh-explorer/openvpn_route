import logging
import os
import ipaddress
import pyroute2

log_file = "/var/log/openvpn/route_helper.log"
table_num = 10

Logger = None


def log_init():
    global Logger
    logger = logging.getLogger("route")
    file_log = logging.FileHandler(log_file)
    file_log.setLevel(logging.INFO)
    fmt = logging.Formatter('[%(levelname)s] %(asctime)s: %(message)s')
    file_log.setFormatter(fmt)
    logger.addHandler(file_log)
    Logger = logger


def convert_route_rule(network: str, netmask: str, gateway: str, metric: str):
    net = ipaddress.IPv4Network((network, netmask))
    net = net.with_prefixlen
    metric = int(metric)
    return net, gateway, metric


# parse route from env
def parse_route():
    i = 0
    routes_list = []
    while True:
        i += 1
        try:
            gateway_key = 'route_gateway_%d' % i
            if gateway_key in os.environ:
                gateway = os.environ[gateway_key]
                netmask = os.environ["route_netmask_%d" % i]
                network = os.environ["route_network_%d" % i]

                metric_key = "route_metric_%d" % i
                if metric_key in os.environ:
                    metric = os.environ[metric_key]
                else:
                    metric = "0"
                routes_list.append(convert_route_rule(network, netmask, gateway, metric))
            else:
                break
        except KeyError as e:
            Logger.error("find a broke route rule, can't find key %s" % str(e))
            continue
    return routes_list


def add_route(ipr, network: str, gateway: str, metric: int):
    ipr.route("add", dst=network, gateway=gateway, priority=metric, table=table_num)


if __name__ == '__main__':
    log_init()
    ipr = pyroute2.IPRoute()
    for network, gateway, metric in parse_route():
        Logger.info("%s via %s metric %d" % (network, gateway, metric))
        add_route(ipr, network, gateway, metric)
    ipr.close()
