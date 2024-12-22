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
          selection = "auto_insert",
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
              -- Method = 2, => Method
              -- Function = 3, => Function
              -- Constructor = 4, => Text
              -- Field = 5, => Constructor
              -- ...
              if kind == type.Field then
                return type.Text
              elseif kind == type.Text then
                return type.Constructor
              elseif kind == type.Constructor then
                return type.Field
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
