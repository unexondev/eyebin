import {
	ResizableHandle,
	ResizablePanel,
	ResizablePanelGroup,
} from "@/components/ui/resizable"

import { Separator } from "@/components/ui/separator"

import StreamPanel from "./components/stream-panel"
import MonitorPanel from "./components/monitor-panel"
import SettingsPanel from "./components/settings-panel"
import FramesPanel from "./components/frames-panel"
import ModelsPanel from "./components/models-panel"
import ScriptsPanel from "./components/scripts-panel"

import { useState } from "react"

import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"

const LeftPanelOption = {
	Stream: 0,
	Monitor: 1,
	Settings: 2
}

const RightPanelOption = {
	Frames: 0,
	Models: 1,
	Scripts: 2
}

export function App() {

	// context states
	const [sensor, setSensor] = useState();

	// navigation states
	const [left_panel_selected, setLeftPanel] = useState(LeftPanelOption.Stream)
	const [right_panel_selected, setRightPanel] = useState(RightPanelOption.Frames)

	let left_panel;
	let right_panel;

	switch (left_panel_selected) {

		case LeftPanelOption.Stream:
			left_panel = <StreamPanel stream_profiles={[]}/>
			break

		case LeftPanelOption.Monitor:
			left_panel = <MonitorPanel/>
			break

		case LeftPanelOption.Settings:
			left_panel = <SettingsPanel/>
			break

	}

	switch (right_panel_selected) {

		case RightPanelOption.Frames:
			right_panel = <FramesPanel/>
			break

		case RightPanelOption.Models:
			right_panel = <ModelsPanel/>
			break

		case RightPanelOption.Scripts:
			right_panel = <ScriptsPanel/>
			break

	}

	return (
		<div className="h-screen">
			<ResizablePanelGroup className="!hidden lg:!flex h-full" orientation="horizontal">
				
				<ResizablePanel className="bg-background h-full">
						
					<div className="flex flex-col h-full">

						<ToggleGroup className="p-3 flex-0">

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Stream);
									}}>
									Stream
								</ToggleGroupItem>
						
								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Monitor);
									}}>
									Monitor
								</ToggleGroupItem>

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Settings);
									}}>
									Settings
								</ToggleGroupItem>

						</ToggleGroup>

						<div className="flex-1 relative left-panel-view">
							{ left_panel }
						</div>

					</div>

				</ResizablePanel>

				<ResizableHandle withHandle/>

				<ResizablePanel>
					
					<div className="flex flex-col h-full">

						<ToggleGroup className="p-3 flex-0">

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setRightPanel(RightPanelOption.Frames);
									}}>
									Frames
								</ToggleGroupItem>
						
								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setRightPanel(RightPanelOption.Models);
									}}>
									Models
								</ToggleGroupItem>

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setRightPanel(RightPanelOption.Scripts);
									}}>
									Scripts
								</ToggleGroupItem>

						</ToggleGroup>

						<div className="flex-1 relative left-panel-view">
							{ right_panel }
						</div>

					</div>

				</ResizablePanel>

			</ResizablePanelGroup>

			<div className="!flex flex-col lg:!hidden min-w-full">
				
				<div className="bg-background">
						
					<div className="flex flex-col">

						<ToggleGroup className="p-3 flex-0">

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Stream);
									}}>
									Stream
								</ToggleGroupItem>
						
								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Monitor);
									}}>
									Monitor
								</ToggleGroupItem>

								<ToggleGroupItem onClick={(e) => {
									e.preventDefault();
									setLeftPanel(LeftPanelOption.Settings);
									}}>
									Settings
								</ToggleGroupItem>

						</ToggleGroup>

						<div className="left-panel-view">
							{ left_panel }
						</div>

					</div>

				</div>

				<Separator/>

				<div className="bg-background">
					
					<ToggleGroup className="p-3">

							<ToggleGroupItem onClick={(e) => {
								e.preventDefault();
								setRightPanel(RightPanelOption.Frames);
								}}>
								Frames
							</ToggleGroupItem>
					
							<ToggleGroupItem onClick={(e) => {
								e.preventDefault();
								setRightPanel(RightPanelOption.Models);
								}}>
								Models
							</ToggleGroupItem>

							<ToggleGroupItem onClick={(e) => {
								e.preventDefault();
								setRightPanel(RightPanelOption.Scripts);
								}}>
								Scripts
							</ToggleGroupItem>

					</ToggleGroup>

					<div className="left-panel-view">
						{ right_panel }
					</div>
				
				</div>

			</div>
		</div>
	)
}

export default App
