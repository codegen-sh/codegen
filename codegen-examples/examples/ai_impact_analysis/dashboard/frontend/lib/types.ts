export interface AnalysisData {
	stats: {
		total_commits: number;
		ai_commits: number;
		ai_percentage: number;
		top_ai_files: [string, number][];
		ai_file_count: number;
		total_file_count: number;
	};
	ai_symbol_count: number;
	total_symbol_count: number;
	high_impact_symbols: HighImpactSymbol[];
	timeline: Timeline[];
	contributors: [string, number][];
}

export interface HighImpactSymbol {
	name: string;
	filepath: string;
	usage_count: number;
	last_editor: string;
}

export interface Timeline {
	date: string;
	count: number;
}
