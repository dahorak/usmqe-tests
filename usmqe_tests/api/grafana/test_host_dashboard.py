"""
REST API test suite - Grafana dashboard host-dashboard
"""

import pytest
import time
from usmqe.api.grafanaapi import grafanaapi
from usmqe.api.graphiteapi import graphiteapi


LOGGER = pytest.get_logger('host_dashboard', module=True)
"""@pylatest default
Setup
=====

Prepare USM cluster accordingly to documentation.
``GRAFANA`` for this file stands for Grafana API url used by tested Tendrl
server.
``GRAPHITE`` for this file stands for Graphite API url used by tested Tendrl
server.

"""

"""@pylatest default
Teardown
========
"""


def test_layout():
    """@pylatest grafana/layout
    API-grafana: layout
    *******************

    .. test_metadata:: author fbalak@redhat.com

    Description
    ===========

    Check that layout of dashboard is according to specification:
    ``https://github.com/Tendrl/specifications/issues/222``
    """
    api = grafanaapi.GrafanaApi()
    """@pylatest grafana/layout
    .. test_step:: 1

        Send **GET** request to:
        ``GRAFANA/dashboards/db/host-dashboard``.

    .. test_result:: 1

        JSON structure containing data related to layout is returned.
    """
    layout = api.get_dashboard("host-dashboard")
    pytest.check(
        len(layout) > 0,
        "cluster-dashboard layout should not be empty")

    """@pylatest grafana/layout
    .. test_step:: 2

        Compare structure of panels and rows as defined in specification:
        ``https://github.com/Tendrl/specifications/issues/222``

    .. test_result:: 2

        Defined structure and structure from Grafana API are equivalent.
    """
    structure_defined = {
        'Network': [
            'Throughput',
            'Dropped Packets Per Second',
            'Errors Per Second'],
        'At-a-Glance': [
            'Health',
            'Bricks',
            'Brick Status',
            'Memory Available',
            'Memory Utilization',
            'Swap Free',
            'Swap Utilization',
            'CPU Utilization',
            'Brick IOPS'],
        'Capacity & Disk Load': [
            'Total Brick Capacity Utilization',
            'Total Brick Capacity Utilization',
            'Total Brick Capacity Available',
            'Weekly Growth Rate',
            'Weeks Remaining',
            'Top Bricks by Capacity Percent Utilized',
            'Top Bricks by Total Capacity',
            'Top Bricks by Capacity Utilized',
            'Disk Throughput',
            'Disk IOPS',
            'Disk IO Latency']}
    structure = {}
    for row in layout["dashboard"]["rows"]:
        structure[row["title"]] = []
        for panel in row["panels"]:
            if panel["title"]:
                structure[row["title"]].append(panel["title"])
            elif "displayName" in panel.keys() and panel["displayName"]:
                structure[row["title"]].append(panel["displayName"])

    LOGGER.debug("defined layout structure = {}".format(structure_defined))
    LOGGER.debug("layout structure in grafana = {}".format(structure))
    pytest.check(
        structure_defined == structure,
        "defined structure of panels should equal to structure in grafana")


def test_cpu_utilization(workload_cpu_utilization, cluster_reuse):
    """@pylatest grafana/cpu_utilization
    API-grafana: cpu_utilization
    *******************

    .. test_metadata:: author fbalak@redhat.com

    Description
    ===========

    Check that Grafana panel *CPU Utilization* is showing correct values.
    """
    # TODO(fbalak): get this number dynamically
    # number of samples from graphite target per minute
    SAMPLE_RATE = 1
    if cluster_reuse["short_name"]:
        cluster_identifier = cluster_reuse["short_name"]
    else:
        cluster_identifier = cluster_reuse["integration_id"]
    grafana = grafanaapi.GrafanaApi()
    graphite = graphiteapi.GraphiteApi()
    """@pylatest grafana/hosts
    .. test_step:: 1
        Send **GET** request to:
        ``GRAFANA/dashboards/db/host-dashboard``.
    .. test_result:: 1
        JSON structure containing data related to layout is returned.
    """

    layout = grafana.get_dashboard("host-dashboard")
    assert len(layout) > 0
    dashboard_rows = layout["dashboard"]["rows"]

    # get CPU Utilization panel from first row
    panels = dashboard_rows[0]["panels"]
    cpu_panels = [
        panel for panel in panels
        if "title" in panel and
        panel["title"] == "CPU Utilization"]
    pytest.check(len(cpu_panels) == 1)

    """@pylatest grafana/cpu_utilization
    .. test_step:: 2
        Send **GET** request to ``GRAPHITE/render?target=[target]&format=json``
        where [target] is part of uri obtained from previous GRAFANA call.
        There should be target for CPU utilization of a host.
        Compare number of hosts from Graphite with value retrieved from
        ``workload_cpu_utilization`` fixture.
    .. test_result:: 2
        JSON structure containing data related to CPU utilization is similar
        to values set by ``workload_cpu_utilization`` fixture in given time.
    """
    # get graphite target pointing at data containing number of host
    target = cpu_panels[0]["targets"][0]["target"]
    target = target.replace("$cluster_id", cluster_identifier)
    target = target.replace("$host_name", pytest.config.getini(
        "usm_cluster_member").replace(".", "_"))
    target = target.strip("aliasSub(groupByNode(")
    target = target.split("},", 1)[0]
    target_base, target_options = target.rsplit(".{", 1)
    target_options = target_options
    LOGGER.debug("target: {}".format(target))
    LOGGER.debug("target_base: {}".format(target_base))
    LOGGER.debug("target_options: {}".format(target_options))
    pytest.check(
        target_options == "percent-user,percent-system",
        "The panel CPU Utilization is composed of user and system parts")
    target_user, target_system = ["{}.{}".format(target_base, x) for x
                                  in target_options.split(",")]
    graphite_user_cpu_data = graphite.get_datapoints(
        target_user,
        from_date=workload_cpu_utilization["start"].strftime("%H:%M_%Y%m%d"),
        until_date=workload_cpu_utilization["end"].strftime("%H:%M_%Y%m%d"))
    graphite_system_cpu_data = graphite.get_datapoints(
        target_system,
        from_date=workload_cpu_utilization["start"].strftime("%H:%M_%Y%m%d"),
        until_date=workload_cpu_utilization["end"].strftime("%H:%M_%Y%m%d"))
    graphite_user_cpu_mean = sum(
        [x[0] for x in graphite_user_cpu_data]) / max(
            len(graphite_user_cpu_data), 1)
    graphite_system_cpu_mean = sum(
        [x[0] for x in graphite_system_cpu_data]) / max(
            len(graphite_system_cpu_data), 1)
    expected_sample_rate =\
        workload_cpu_utilization["end"] - workload_cpu_utilization["start"]
    expected_sample_rate =\
        time.mktime(expected_sample_rate.timetuple()) * SAMPLE_RATE
    pytest.check(
        (len(graphite_user_cpu_data) == expected_sample_rate) or
        (len(graphite_user_cpu_data) == expected_sample_rate - 1),
        "Number of samples of user data should be {}, is {}.".format(
            expected_sample_rate, len(graphite_user_cpu_data)))
    pytest.check(
        (len(graphite_system_cpu_data) == expected_sample_rate) or
        (len(graphite_system_cpu_data) == expected_sample_rate - 1),
        "Number of samples of system data should be {}, is {}.".format(
            expected_sample_rate, len(graphite_system_cpu_data)))
    LOGGER.debug("CPU user utilization in Graphite: {}".format(
        graphite_user_cpu_mean))
    LOGGER.debug("CPU system utilization in Graphite: {}".format(
        graphite_system_cpu_mean))
    divergence = 10
    minimal_cpu_utilization = workload_cpu_utilization["result"] - divergence
    maximal_cpu_utilization = workload_cpu_utilization["result"] + divergence
    graphite_cpu_mean = graphite_user_cpu_mean + graphite_system_cpu_mean
    pytest.check(
        minimal_cpu_utilization < graphite_cpu_mean < maximal_cpu_utilization,
        "CPU should be {}, CPU in Graphite is: {}, \
applicable divergence is {}".format(
            workload_cpu_utilization["result"],
            graphite_cpu_mean,
            divergence))
