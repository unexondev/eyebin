import axios from "axios"
import { api } from "./lib/api"
import type { AppContext, AppActions, SensorResponse } from "./lib/defs"
import { AppState } from "./lib/defs"

import { Separator } from "@/components/ui/separator"
import {
  Alert,
  AlertDescription,
  AlertTitle,
} from "@/components/ui/alert"
import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group"

import StreamPanel from "@/components/stream-panel"
import MonitorPanel from "@/components/monitor-panel"
import SettingsPanel from "@/components/settings-panel"
import FramesPanel from "@/components/frames-panel"
import ModelsPanel from "@/components/models-panel"
import ScriptsPanel from "@/components/scripts-panel"

import { useEffect, useState } from "react"

import { CgSpinnerTwoAlt } from "react-icons/cg";
import { CiWarning } from "react-icons/ci";
import { IoIosNotificationsOutline } from "react-icons/io";


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

	// application state	
	const [app_context, setAppContext] = useState<AppContext>({
		state: AppState.Loading,
		last_errors: [],
		last_notifications: []
	});

	function setLoading() {
		setAppContext(prev => ({
			...prev,
			state: AppState.Loading
		}))
	}

	function setReady() {
		setAppContext(prev => ({
			...prev,
			state: AppState.Ready
		}))
	}

	function setErrored() {
		setAppContext(prev => ({
			...prev,
			state: AppState.Errored
		}))
	}

	function pushError(message: string) {
		const id = crypto.randomUUID();

		setAppContext(prev => ({
			...prev,
			last_errors: [
				...prev.last_errors,
				{ id, message }
			],
		}));
		
		setTimeout(() => {

			setAppContext(prev => ({
				...prev,
				last_errors: prev.last_errors.filter(error => error.id !== id),
			}));

		}, 5000);
	}

	function pushNotification(message: string) {
		const id = crypto.randomUUID();

		setAppContext(prev => ({
			...prev,
			last_notifications: [
				...prev.last_notifications,
				{ id, message }
			],
		}));
		
		setTimeout(() => {

			setAppContext(prev => ({
				...prev,
				last_notifications: prev.last_notifications.filter(notification => notification.id !== id),
			}));

		}, 5000);
	}

	const appActions : AppActions = {
		setLoading,
		setReady,
		setErrored,
		pushError,
		pushNotification
	}

	// context states
	const [sensors, setSensors] = useState<SensorResponse[] | null>(null);

	// navigation states
	const [left_panel_selected, setLeftPanel] = useState(LeftPanelOption.Stream)
	const [right_panel_selected, setRightPanel] = useState(RightPanelOption.Frames)

	let left_panel;
	let right_panel;

	switch (left_panel_selected) {

		case LeftPanelOption.Stream:
			left_panel = <StreamPanel appActions={appActions} sensors={sensors} loadSensors={loadSensors}/>
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

	async function loadSensors() {

		appActions.setLoading()

		try {
			
			const res = await api.get<SensorResponse[]>("/sensor/fetch");
			
			setSensors(res.data);
			
		} catch (error: any) {
			
			if (axios.isAxiosError(error)) {
				appActions.pushError(
					error.response?.data?.detail ??
					"An error occured while establishing connection."
				);
			}

			else {
				appActions.pushError("An unexpected error occured.");
			}
		
		}

		finally {

			appActions.setReady();

		}

	}

	useEffect(() => {

		appActions.pushNotification("Welcome! We strongly recommend reading our documentation before starting.")

		loadSensors();

	}, []);

	useEffect(() => {

		if (sensors === null) return;

		appActions.pushNotification("Sensors are fetched successfully.");

	}, [sensors])

	return (
		<div className="h-screen">
			{
				app_context.state == AppState.Loading ? (
					<div className="fixed inset-0 bg-black/75 z-[9999] flex items-center justify-center">
						<CgSpinnerTwoAlt className="animate-spin" size="2.5rem"/>
					</div>
				) : (
					<div className="fixed right-4 top-4 flex flex-row gap-2 z-[9998]">
						<div className="flex flex-col gap-3">
							{
								app_context.last_errors.map(err => (

									<Alert key={err.id}
										className="border-amber-900 bg-amber-950 text-amber-50 animate-in fade-in-0 zoom-in-95 p-3 w-75">
										<CiWarning/>	
										<AlertTitle>Error</AlertTitle>
										<AlertDescription>
											{ err.message }
										</AlertDescription>
									</Alert>

								))
							}
						</div>
						<div className="flex flex-col gap-3">
							{
								app_context.last_notifications.map(err => (

									<Alert key={err.id}
										className="border-green-900 bg-green-950 text-green-50 animate-in fade-in-0 zoom-in-95 p-3 w-75">
										<IoIosNotificationsOutline/>
										<AlertTitle>Notification</AlertTitle>
										<AlertDescription>
											{ err.message }
										</AlertDescription>
									</Alert>

								))
							}
						</div>
					</div>
				)
			}
			
			<div className="flex flex-col min-w-full lg:flex-row lg:h-full">
				
				<div className="flex flex-col lg:h-full lg:flex-1">

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

				<Separator orientation="vertical" className="hidden lg:block"/>
				<Separator orientation="horizontal" className="lg:hidden"/>
					
				<div className="flex flex-col lg:h-full lg:w-1/2">

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

					<div className="flex-1 relative left-panel-view">
						{ right_panel }
					</div>

				</div>

			</div>

		</div>
	)
}

export default App
