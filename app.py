"""
Gradio UI for FitFindr.
"""

import gradio as gr

from agent import run_agent
from utils.data_loader import get_empty_wardrobe, get_example_wardrobe


def _listing_block(item: dict) -> str:
    rows = [
        item["title"],
        f"${item['price']:g} · {item['size']} · {item['condition']}",
        f"Sold on {item['platform']}",
    ]
    if item.get("brand"):
        rows.append(f"Brand: {item['brand']}")
    if item.get("colors"):
        rows.append("Colors: " + ", ".join(item["colors"]))
    if item.get("description"):
        rows.append("")
        rows.append(item["description"])
    return "\n".join(rows)


def handle_query(user_query: str, wardrobe_choice: str) -> tuple[str, str, str]:
    if not user_query or not user_query.strip():
        return "Type what you're thrifting for to get started.", "", ""

    wardrobe = (
        get_empty_wardrobe()
        if wardrobe_choice == "Empty wardrobe (new user)"
        else get_example_wardrobe()
    )

    session = run_agent(user_query, wardrobe)

    if session["error"]:
        return session["error"], "", ""

    listing = _listing_block(session["selected_item"])
    if session.get("price_assessment"):
        listing += "\n\n💰 " + session["price_assessment"]["message"]

    return listing, session["outfit_suggestion"], session["fit_card"]


EXAMPLES = [
    ["vintage graphic tee under $30", "Example wardrobe"],
    ["90s track jacket in size M", "Example wardrobe"],
    ["flowy midi skirt under $40", "Example wardrobe"],
    ["black combat boots size 8", "Example wardrobe"],
    ["designer ballgown size XXS under $5", "Example wardrobe"],
]


def build_interface() -> gr.Blocks:
    with gr.Blocks(title="FitFindr") as demo:
        gr.Markdown(
            "# FitFindr\n"
            "Describe a thrift find — add size and budget if you want filters."
        )

        with gr.Row():
            query = gr.Textbox(
                label="What are you looking for?",
                placeholder="e.g. vintage graphic tee under $30, size M",
                lines=2,
                scale=3,
            )
            wardrobe_radio = gr.Radio(
                choices=["Example wardrobe", "Empty wardrobe (new user)"],
                value="Example wardrobe",
                label="Wardrobe",
                scale=1,
            )

        go = gr.Button("Find it", variant="primary")

        with gr.Row():
            panel_listing = gr.Textbox(label="Top listing", lines=8, interactive=False)
            panel_outfit = gr.Textbox(label="Outfit idea", lines=8, interactive=False)
            panel_card = gr.Textbox(label="Fit card", lines=8, interactive=False)

        gr.Examples(examples=EXAMPLES, inputs=[query, wardrobe_radio])

        outputs = [panel_listing, panel_outfit, panel_card]
        go.click(handle_query, [query, wardrobe_radio], outputs)
        query.submit(handle_query, [query, wardrobe_radio], outputs)

    return demo


if __name__ == "__main__":
    build_interface().launch()
