require("neotest").setup({
    adapters = {
        require("neotest-python")({
            dap = { justMyCode = false },
        }),
        require('neotest-dart') {
            command = 'flutter', -- Command being used to run tests. Defaults to `flutter`
                                 -- Change it to `fvm flutter` if using FVM
                                 -- change it to `dart` for Dart only tests
            use_lsp = true       -- When set Flutter outline information is used when constructing test name.
        },
        require("neotest-rust"),
    },
})
