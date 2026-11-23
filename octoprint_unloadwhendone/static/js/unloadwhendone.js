$(function () {
    function UnloadWhenDoneViewModel(parameters) {
        var self = this;
        self.loginState = parameters[0];
        self.access = parameters[1];
        self.armed = ko.observable(false);
        self.busy = ko.observable(false);

        self.canControl = ko.pureComputed(function () {
            return self.loginState.hasPermission(self.access.permissions.PRINT);
        });

        self.title = ko.pureComputed(function () {
            return self.armed()
                ? "Filament WILL be unloaded after this print. Click to cancel."
                : "Unload the filament after this print finishes successfully";
        });

        self.toggle = function () {
            if (self.busy()) return;
            self.busy(true);
            OctoPrint.simpleApiCommand("unloadwhendone", "toggle", {})
                .done(function (r) { self.armed(r.armed); })
                .always(function () { self.busy(false); });
        };

        self.refresh = function () {
            OctoPrint.simpleApiGet("unloadwhendone").done(function (r) { self.armed(r.armed); });
        };

        self.onDataUpdaterPluginMessage = function (plugin, data) {
            if (plugin !== "unloadwhendone") return;
            self.armed(!!data.armed);
        };

        // Put our toggle right under Print / Pause / Cancel in the State panel.
        self.injectStateButton = function () {
            var anchor = $("#state_wrapper .print-control").first();
            if (!anchor.length || $("#uwd_state_row").length) return;
            var row = $(
                '<div id="uwd_state_row" class="row-fluid" data-bind="visible: canControl">' +
                '  <button class="btn btn-block uwd-state-btn" ' +
                '          data-bind="click: toggle, enable: !busy(), css: {\'btn-warning active\': armed}, attr: {title: title}">' +
                '    <i class="far" data-bind="css: {\'fa-check-square\': armed, \'fa-square\': !armed()}"></i>' +
                '    <i class="fas fa-eject"></i> Unload filament after print' +
                '  </button>' +
                '</div>'
            );
            anchor.after(row);
            ko.applyBindings(self, row[0]);
        };

        self.onStartupComplete = function () {
            self.injectStateButton();
            self.refresh();
        };
        self.onUserLoggedIn = self.refresh;
    }

    OCTOPRINT_VIEWMODELS.push({
        construct: UnloadWhenDoneViewModel,
        dependencies: ["loginStateViewModel", "accessViewModel"],
        elements: ["#navbar_plugin_unloadwhendone"]
    });
});
