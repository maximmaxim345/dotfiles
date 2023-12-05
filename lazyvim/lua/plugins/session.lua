return {
  {
    "jedrzejboczar/possession.nvim",
    dependencies = {
      "nvim-lua/plenary.nvim",
    },
    config = function()
      local function close_session()
        local session = require("possession.session")
        if session.session_name then
          session.autosave()
          session.close()
        else
          -- close all buffers
          vim.api.nvim_command("bufdo bd!")
        end
      end

      local function has_unsaved_changes()
        -- test all buffers for unsaved changes
        local unsaved = false
        for _, buf in ipairs(vim.api.nvim_list_bufs()) do
          if vim.api.nvim_buf_get_option(buf, "modified") then
            unsaved = true
            break
          end
        end
        return unsaved
      end

      local function kill_all_terminals()
        for _, buf in ipairs(vim.api.nvim_list_bufs()) do
          if vim.api.nvim_buf_get_option(buf, "buftype") == "terminal" then
            vim.api.nvim_buf_delete(buf, { force = true })
          end
        end
      end

      -- return true if changes were saved or discarded
      local function ask_unsaved_changes()
        if has_unsaved_changes() then
          -- Ask a dialog to discard changes
          -- local choice = vim.fn.input({
          --   prompt = "You have unsaved changes. Save them, discard or cancel? (s/d/c): ",
          --   cancelreturn = "c",
          -- })
          local choice = vim.fn.confirm("You have unsaved changes.", "&Save\n&Discard\n&Cancel")
          if choice == 1 then
            -- save all buffers
            vim.api.nvim_command("wa")
          elseif choice == 2 then
            -- discard all changes
            vim.api.nvim_command("bufdo e!")
          else
            -- cancel, do nothing
            return false
          end
        end
        return true
      end

      vim.api.nvim_create_user_command("SClose", function()
        if not ask_unsaved_changes() then
          return
        end
        kill_all_terminals()
        close_session()
        vim.api.nvim_command("nohlsearch")
        vim.opt.spell = false
        vim.opt.wrap = false
        vim.g.neovide_fullscreen = false
        -- TODO: default font/theme
        -- require("alpha-cfg").alpha_load_buttons()
        require("alpha").start(false)
      end, {})

      vim.api.nvim_create_user_command("SQuit", function()
        if not ask_unsaved_changes() then
          return
        end
        kill_all_terminals()
        close_session()
        vim.api.nvim_command("qa")
      end, {})

      require("possession").setup({
        prompt_no_cr = true,
        silent = true,
        autosave = {
          current = true, -- or fun(name): boolean
          tmp = false, -- or fun(): boolean
          tmp_name = "tmp",
          on_load = true,
          on_quit = true,
        },
        commands = {
          save = "SSave",
          load = "SLoad", -- open last session
          delete = "SDelete",
          close = "PossessionClose",
          show = "PossessionShow",
          list = "PossessionList",
          migrate = "PossessionMigrate",
        },
        hooks = {
          before_save = function(name)
            local user_data = {}
            user_data.font_size = GUIFONT.font_size
            user_data.theme = vim.g.colors_name
            user_data.neovide = {
              fullscreen = vim.g.neovide_fullscreen,
            }
            -- Barbar dumps its data only after SessionSavePre is fired.
            vim.cmd("doautocmd User SessionSavePre")
            -- user_data.barbar_session_restore = vim.g.Bufferline__session_restore
            return user_data
          end,
          after_save = function(name, user_data, aborted)
            -- This is a workaround for a bug, where barbar doesn't update the buffer list when a buffer is deleted.
            -- Otherwise, it tries to lookup a invalid buffer id.
            -- local state = require("barbar.state")
            -- state.buffers = {}
          end,
          before_load = function(name, user_data)
            -- close all buffers
            vim.api.nvim_command("bufdo bd!")
            if user_data.theme then
              vim.cmd("colorscheme " .. user_data.theme)
            end
            if user_data.font_size then
              GUIFONT.set_font_size(user_data.font_size, true)
            end
            if user_data.neovide then
              vim.g.neovide_fullscreen = user_data.neovide.fullscreen
            end
            -- if user_data.barbar_session_restore then
            --   vim.g.Bufferline__session_restore = user_data.barbar_session_restore
            -- end
            return user_data
          end,
          after_load = function(name, user_data)
            -- -- reload nvim_tree cwd
            -- require("nvim-tree.api").tree.change_root(vim.loop.cwd())
            -- restore barbar session
            vim.cmd("doautocmd SessionLoadPost")
          end,
        },
        plugins = {
          close_windows = {
            hooks = { "before_save", "before_load" },
            preserve_layout = true, -- or fun(win): boolean
            match = {
              floating = true,
              buftype = {
                "terminal",
              },
              filetype = {},
              custom = false, -- or fun(win): boolean
            },
          },
          delete_hidden_buffers = false,
          nvim_tree = true,
          -- tabby = true,
          delete_buffers = false,
        },
      })
      require("telescope").load_extension("possession")
    end,
    lazy = false,
    keys = {
      { "<leader>qc", "<cmd>SClose<CR>", desc = "Close the current session" },
      { "<leader>qo", "<cmd>Telescope possession list<CR>", desc = "Open a session" },
      { "<leader>qq", "<cmd>SQuit<CR>", desc = "Quit" },
    },
  },
  {
    "goolord/alpha-nvim",
    optional = true,
    opts = function(_, dashboard)
      local button = dashboard.button("p", " " .. " Projects", ":Telescope possession list<CR>")
      button.opts.hl = "AlphaButtons"
      button.opts.hl_shortcut = "AlphaShortcut"
      table.insert(dashboard.section.buttons.val, 1, button)
    end,
  },
}
