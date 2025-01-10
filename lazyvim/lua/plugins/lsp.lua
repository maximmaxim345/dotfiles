return {
  {
    "neovim/nvim-lspconfig",
    opts = {
      inlay_hints = { enabled = true },
    },
  },
  {
    "saghen/blink.cmp",
    opts = {
      keymap = {
        preset = "enter",
        ["<Tab>"] = {
          "select_next",
          "fallback",
        },
        ["<S-Tab>"] = {
          "select_prev",
          "fallback",
        },
      },
      completion = {
        list = {
          max_items = 200,
          selection = {
            preselect = false,
            auto_insert = true,
          },
          cycle = {
            from_bottom = true,
          },
        },
        documentation = {
          auto_show = true,
          auto_show_delay_ms = 500,
        },
      },
      signature = {
        enabled = true,
      },
      fuzzy = {
        sorts = {
          function(a, b)
            local type = require("blink.cmp.types").CompletionItemKind

            local function rerank(kind)
              -- Reranks completion options according to my preference:
              -- Text = 1, => Field
              -- Method = 2, => Variable
              -- Function = 3, => Method
              -- Constructor = 4, => Function
              -- Field = 5, => Text
              -- Variable = 6 => Constructor
              -- ...
              if kind == type.Field then
                return type.Text
              elseif kind == type.Variable then
                return type.Method
              elseif kind == type.Method then
                return type.Function
              elseif kind == type.Function then
                return type.Constructor
              elseif kind == type.Text then
                return type.Field
              elseif kind == type.Constructor then
                return type.Variable
              else
                return kind
              end
            end
            local a_kind = rerank(a.kind)
            local b_kind = rerank(b.kind)
            if a_kind == b_kind then
              return
            end
            return a_kind < b_kind
          end,
          "score",
          "sort_text",
        },
      },
    },
  },
}
