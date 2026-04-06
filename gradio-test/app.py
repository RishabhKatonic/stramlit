"""
Katonic App Deployment — Gradio Test App
Framework: Gradio | Port: 7860
Run: python app.py
"""
import gradio as gr
import datetime
import os


def greet(name, intensity):
    return (
        f"Hello, {name}! {'🎉' * int(intensity)}\n\n"
        f"✅ Gradio is running successfully on Katonic!\n"
        f"Hostname: {os.getenv('HOSTNAME', 'unknown')}\n"
        f"Timestamp: {datetime.datetime.now().isoformat()}"
    )


def reverse_text(text):
    return text[::-1]


def calculate(a, b, operation):
    ops = {
        "Add": a + b,
        "Subtract": a - b,
        "Multiply": a * b,
        "Divide": a / b if b != 0 else "Error: Division by zero",
    }
    return f"Result: {ops[operation]}"


with gr.Blocks(title="Katonic Gradio Test") as demo:
    gr.Markdown("# 🚀 Katonic Gradio Test App")
    gr.Markdown("✅ **Gradio is running successfully on Katonic!**")

    with gr.Tab("Greeter"):
        name_input = gr.Textbox(label="Your Name", value="Katonic User")
        intensity = gr.Slider(1, 10, value=3, step=1, label="Excitement Level")
        greet_output = gr.Textbox(label="Output")
        greet_btn = gr.Button("Say Hello")
        greet_btn.click(greet, inputs=[name_input, intensity], outputs=greet_output)

    with gr.Tab("Text Reverser"):
        text_input = gr.Textbox(label="Enter text", value="Katonic AI Platform")
        reversed_output = gr.Textbox(label="Reversed")
        reverse_btn = gr.Button("Reverse")
        reverse_btn.click(reverse_text, inputs=text_input, outputs=reversed_output)

    with gr.Tab("Calculator"):
        with gr.Row():
            num_a = gr.Number(label="A", value=10)
            num_b = gr.Number(label="B", value=5)
        op = gr.Radio(["Add", "Subtract", "Multiply", "Divide"], label="Operation", value="Add")
        calc_output = gr.Textbox(label="Result")
        calc_btn = gr.Button("Calculate")
        calc_btn.click(calculate, inputs=[num_a, num_b, op], outputs=calc_output)

    gr.Markdown(f"---\nKatonic App Deployment Test | {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

demo.launch(server_name="0.0.0.0", server_port=7860)
