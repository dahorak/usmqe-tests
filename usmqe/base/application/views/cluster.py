from widgetastic.widget import (Text, TextInput, View)

from usmqe.base.application.views.common import BaseLoggedInView
from usmqe.base.application.widgets import Kebab
from taretto.ui.patternfly import Button, Dropdown
from widgetastic.widget import ParametrizedLocator, ParametrizedView


class ClustersView(BaseLoggedInView):
    """List of clusters
    There's no list-group widget, so it had to be a parametrized view.
    """

    @ParametrizedView.nested
    class clusters(ParametrizedView):
        PARAMETERS = ("cluster_id",)
        ALL_CLUSTERS = ".//div[@class='list-group-item']"
        ALL_CLUSTER_IDS = ".//div[@class='list-view-pf-description']/descendant-or-self::*/text()"
        ROOT = ParametrizedLocator(
            "//div/*[text()[normalize-space(.)]={cluster_id|quote}]/ancestor-or-self::" +
            "div[@class='list-group-item']")

        cluster_version = Text(".//div[text() = 'Cluster Version']/following-sibling::h5")
        managed = Text(".//div[text() = 'Managed']/following-sibling::h5")
        hosts = Text(".//div[text() = 'Hosts']/following-sibling::h5")
        volumes = Text(".//div[text() = 'Volumes']/following-sibling::h5")
        alerts = Text(".//div[text() = 'Alerts']/following-sibling::h5")
        profiling = Text(".//div[text() = 'Volume Profiling']/following-sibling::h5")
        status = Text(".//div[@class='list-view-pf-additional-info-item cluster-text']")
        import_button = Button("contains", "Import")
        dashboard_button = Button("Dashboard")
        actions = Kebab()

        @classmethod
        def all(cls, browser):
            return [(browser.text(e),) for e in browser.elements(cls.ALL_CLUSTER_IDS)]

    ALL_CLUSTER_IDS = ".//div[@class='list-view-pf-description']"

    # TODO: fix dropdown. If clicked, dropdown changes its name and won't be found anymore
    pagename = Text(".//h1")
    filter_type = Dropdown("Name")
    # TextInput can't be defined by placeholder
    # user_filter = TextInput(placeholder='Filter by Name')

    @property
    def all_ids(self):
        return [self.browser.text(e) for e in self.browser.elements(self.ALL_CLUSTER_IDS)
                if self.browser.text(e) is not None and self.browser.text(e) != '']

    @property
    def is_displayed(self):
        return self.pagename.text == "Clusters"


class UnmanageConfirmationView(View):
    ROOT = ".//pf-modal-overlay-content"
    # close_alert = 
    alert_name = Text(".//h4")
    cancel = Button("Cancel")
    unmanage = Button("Unmanage")


class UnmanageTaskSubmittedView(View):
    ROOT = ".//pf-modal-overlay-content"
    CLOSE_LOC = './/div[@class="modal-header"]/button[@class="close ng-scope"]'
    view_progress = Button("contains", "View Task Progress")

    def close(self):
        """Close the modal"""
        self.browser.click(self.CLOSE_LOC, parent=self)
