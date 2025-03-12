import { Code2 } from "lucide-react";

export function DashboardHeader() {
	return (
		<div className="flex justify-between items-center mt-10 mb-10">
			<div className="flex flex-col space-y-2">
				<div className="flex items-center space-x-2">
					<h1 className="text-2xl font-bold tracking-tight">
						AI Code Impact Analysis
					</h1>
				</div>
				<p className="text-muted-foreground">
					Analyze AI-generated code contributions in your repository
				</p>
			</div>
		</div>
	);
}
