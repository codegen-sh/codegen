import { Loader2 } from "lucide-react";

export function LoadingScreen() {
	return (
		<div className="fixed inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center">
			<div className="text-center space-y-4">
				<Loader2 className="h-16 w-16 animate-spin text-primary mx-auto" />
				<h2 className="text-2xl font-bold text-foreground">
					Analyzing Repository
				</h2>
				<p className="text-muted-foreground">This may take a few seconds...</p>
			</div>
		</div>
	);
}
