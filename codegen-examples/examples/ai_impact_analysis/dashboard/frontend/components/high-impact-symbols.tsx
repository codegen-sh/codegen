import {
	Card,
	CardContent,
	CardDescription,
	CardHeader,
	CardTitle,
} from "@/components/ui/card";
import { ScrollArea } from "@/components/ui/scroll-area";
import type { HighImpactSymbol } from "@/lib/types";

interface HighImpactSymbolsProps {
	symbols: HighImpactSymbol[];
}

export function HighImpactSymbols({ symbols }: HighImpactSymbolsProps) {
	return (
		<Card className="col-span-1">
			<CardHeader>
				<CardTitle>High-Impact AI Symbols</CardTitle>
				<CardDescription>
					AI-written code with significant usage
				</CardDescription>
			</CardHeader>
			<CardContent>
				<ScrollArea className="h-[300px] pr-4">
					<div className="space-y-4">
						{symbols.length > 0 ? (
							symbols.map((symbol) => (
								<div
									key={symbol.name}
									className="space-y-2 rounded-md border p-3"
								>
									<div className="flex justify-between">
										<div className="font-medium">{symbol.name}</div>
										<div className="text-sm text-muted-foreground">
											Used by {symbol.usage_count} symbols
										</div>
									</div>
									<div className="text-xs text-muted-foreground">
										{symbol.filepath}
									</div>
									<div className="text-xs">
										Last edited by:{" "}
										<span className="font-medium">{symbol.last_editor}</span>
									</div>
								</div>
							))
						) : (
							<div className="flex h-[200px] items-center justify-center text-muted-foreground">
								No high-impact AI symbols found
							</div>
						)}
					</div>
				</ScrollArea>
			</CardContent>
		</Card>
	);
}
