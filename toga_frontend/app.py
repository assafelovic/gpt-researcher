from __future__ import annotations

from toga import App, Box, Button, Label, MainWindow, MultilineTextInput, ScrollContainer, TextInput
from toga.style import Pack
from toga.style.pack import CENTER, COLUMN, ROW

from toga_frontend.api_client import ResearchClient, ResearchError
from toga_frontend.components.settings_dialog import SettingsWindow


class GPTResearcherApp(App):
    def __init__(self):
        super().__init__(formal_name="GPT Researcher", app_id="org.gptresearcher", app_name="GPT Researcher")
        self.client: ResearchClient = ResearchClient()

    def startup(self):
        self.main_window: MainWindow = MainWindow(title=self.formal_name)
        self.main_box: Box = Box(style=Pack(direction=COLUMN, padding=10))

        # Query input section
        input_box = Box(style=Pack(direction=ROW, padding=5, alignment=CENTER))
        self.query_input: TextInput = TextInput(placeholder="Enter your research query", style=Pack(flex=1, padding_right=5, width=400))
        self.submit_button: Button = Button("Research", on_press=self.handle_research, style=Pack(padding_left=5, width=100))
        self.settings_button: Button = Button(
            "⚙",  # Gear icon
            on_press=self.show_settings,
            style=Pack(padding_left=5, width=40),
        )
        input_box.add(self.query_input)
        input_box.add(self.submit_button)
        input_box.add(self.settings_button)

        # Status section
        self.status_label: Label = Label("Ready to research", style=Pack(padding=(0, 5), alignment=CENTER))

        # Results section
        results_container = ScrollContainer(style=Pack(flex=1))
        self.results_box: Box = Box(style=Pack(direction=COLUMN, padding=5))
        self.results_content: MultilineTextInput = MultilineTextInput(readonly=True, style=Pack(flex=1, padding=5, height=400))
        self.results_box.add(self.results_content)
        results_container.content = self.results_box

        # Add all sections to main box
        self.main_box.add(input_box)
        self.main_box.add(self.status_label)
        self.main_box.add(results_container)

        # Set main window size and content
        self.main_window.size = (800, 600)
        self.main_window.content = self.main_box
        self.main_window.show()

    def show_settings(self, widget: Button):
        """Show the settings window."""
        settings_window = SettingsWindow(self, on_save=self.handle_settings_save)
        settings_window.show()

    def handle_settings_save(self):
        """Handle settings save event."""
        try:
            # Reinitialize client with new settings
            self.client = ResearchClient()
            self.status_label.text = "Settings saved successfully"
        except ResearchError as e:
            self.status_label.text = str(e)

    async def handle_research(self, widget: Button):
        """Handle research button press."""
        query = self.query_input.value
        if not query:
            self.status_label.text = "Please enter a research query"
            return

        # Update UI state
        self.submit_button.enabled = False
        self.settings_button.enabled = False
        self.status_label.text = "Researching..."
        self.results_content.value = "Conducting research, please wait..."

        try:
            # Conduct research
            results = await self.client.submit_research(query)

            # Format and display results
            report = results["report"]
            sources = results["sources"]
            costs = results["costs"]

            output = f"Research Report\n\n{report}\n\nSources:\n"
            for source in sources:
                output += f"- {source}\n"
            output += f"\nTotal cost: ${costs:.4f}"

            self.results_content.value = output
            self.status_label.text = "Research complete"

        except ResearchError as e:
            self.status_label.text = f"Error: {str(e)}"
            self.results_content.value = f"An error occurred: {str(e)}"
        except Exception as e:
            self.status_label.text = "An unexpected error occurred"
            self.results_content.value = f"An unexpected error occurred: {str(e)}"

        finally:
            self.submit_button.enabled = True
            self.settings_button.enabled = True


def main() -> GPTResearcherApp:
    return GPTResearcherApp()


if __name__ == "__main__":
    app = main()
    app.main_loop()
