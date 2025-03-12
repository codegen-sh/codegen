import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { ScrollArea } from "@/components/ui/scroll-area";

interface TopAIFilesProps {
	files: [string, number][];
}

export function TopAIFiles({ files }: TopAIFilesProps) {
	return (
		<Card className="col-span-1">
			<CardHeader>
				<CardTitle>Top AI-Contributed Files</CardTitle>
				<CardDescription>
					Files with highest AI contribution percentage
				</CardDescription>
			</CardHeader>
			<CardContent>
				<ScrollArea className="h-[300px] pr-4">
					<div className="space-y-4">
						{files.map(([filepath, percentage]) => (
							<div key={filepath} className="space-y-1">
								<div className="flex justify-between text-sm">
									<div className="truncate font-medium">
										{filepath.split("/").pop()}
									</div>
									<div className="text-muted-foreground">
										{percentage.toFixed(1)}%
									</div>
								</div>
								<Progress value={percentage} className="h-2" />
								<div className="text-xs text-muted-foreground truncate">
									{filepath}
								</div>
							</div>
						))}
					</div>
				</ScrollArea>
			</CardContent>
		</Card>
	);
}
