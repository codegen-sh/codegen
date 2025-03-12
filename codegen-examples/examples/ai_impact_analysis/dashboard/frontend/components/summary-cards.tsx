import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { AnalysisData } from "@/lib/types";
import { BarChart3, FileCode, GitCommit, Percent } from "lucide-react";

interface SummaryCardsProps {
	data: AnalysisData;
}

export function SummaryCards({ data }: SummaryCardsProps) {
	const { stats, ai_symbol_count, total_symbol_count } = data;

	return (
		<div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
			<Card>
				<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle className="text-sm font-medium">AI Commits</CardTitle>
					<GitCommit className="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div className="text-2xl font-bold">
						{stats.ai_commits} / {stats.total_commits}
					</div>
					<p className="text-xs text-muted-foreground">
						{stats.ai_percentage.toFixed(1)}% of total commits
					</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle className="text-sm font-medium">AI Files</CardTitle>
					<FileCode className="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div className="text-2xl font-bold">
						{stats.ai_file_count} / {stats.total_file_count}
					</div>
					<p className="text-xs text-muted-foreground">
						{((stats.ai_file_count / stats.total_file_count) * 100).toFixed(1)}%
						of files have &gt;50% AI contribution
					</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle className="text-sm font-medium">AI Symbols</CardTitle>
					<BarChart3 className="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div className="text-2xl font-bold">
						{ai_symbol_count} / {total_symbol_count}
					</div>
					<p className="text-xs text-muted-foreground">
						{((ai_symbol_count / total_symbol_count) * 100).toFixed(1)}% of code
						symbols
					</p>
				</CardContent>
			</Card>

			<Card>
				<CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
					<CardTitle className="text-sm font-medium">High Impact</CardTitle>
					<Percent className="h-4 w-4 text-muted-foreground" />
				</CardHeader>
				<CardContent>
					<div className="text-2xl font-bold">
						{data.high_impact_symbols.length}
					</div>
					<p className="text-xs text-muted-foreground">
						AI-written symbols with high usage
					</p>
				</CardContent>
			</Card>
		</div>
	);
}
