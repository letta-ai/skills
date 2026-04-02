/**
 * LLM-Based Sentiment Analysis (TypeScript)
 *
 * A standalone, multi-source sentiment analysis module that uses an LLM (Claude)
 * to classify text sentiment with source-aware calibration. Designed for
 * Next.js / Node.js data pipelines processing content from Reddit, Hacker News,
 * news articles, academic papers, and more.
 *
 * Requires the `@anthropic-ai/sdk` package and Node 18+ (for native fetch).
 *
 * @example
 * ```ts
 * import { SentimentAnalyzer } from "./sentiment";
 *
 * const analyzer = new SentimentAnalyzer();
 * const result = await analyzer.analyze("This product is amazing!", "review");
 * console.log(result.sentiment, result.confidence, result.reasoning);
 * ```
 *
 * @example
 * ```ts
 * import { analyzeSentiment } from "./sentiment";
 *
 * const result = await analyzeSentiment("Great update!", "reddit");
 * ```
 */

import Anthropic from "@anthropic-ai/sdk";
import { readFileSync } from "fs";
import { resolve, dirname } from "path";
import { fileURLToPath } from "url";

// ── Types ───────────────────────────────────────────────────────────

export type Sentiment = "positive" | "negative" | "neutral" | "mixed";

export type Source =
  | "reddit"
  | "hackernews"
  | "news"
  | "academic"
  | "social_media"
  | "review"
  | "general";

const VALID_SENTIMENTS = new Set<string>([
  "positive",
  "negative",
  "neutral",
  "mixed",
]);

const VALID_SOURCES = new Set<string>([
  "reddit",
  "hackernews",
  "news",
  "academic",
  "social_media",
  "review",
  "general",
]);

// ── Configuration ───────────────────────────────────────────────────

export interface SentimentConfig {
  /** Claude model to use (default: claude-sonnet-4-6). */
  model?: string;
  /** Maximum response tokens (default: 256). */
  maxTokens?: number;
  /** Sampling temperature (default: 0 for deterministic). */
  temperature?: number;
  /** Anthropic API key. Falls back to ANTHROPIC_API_KEY env var. */
  apiKey?: string;
  /** Source to use when none is specified (default: general). */
  defaultSource?: Source;
  /** Truncate input text beyond this length (default: 4000). */
  maxTextLength?: number;
}

interface ResolvedConfig {
  model: string;
  maxTokens: number;
  temperature: number;
  apiKey: string | undefined;
  defaultSource: Source;
  maxTextLength: number;
}

// ── Result ──────────────────────────────────────────────────────────

export interface SentimentResult {
  /** One of positive, negative, neutral, or mixed. */
  sentiment: Sentiment;
  /** Confidence score between 0.0 and 1.0. */
  confidence: number;
  /** Brief explanation of the classification. */
  reasoning: string;
  /** The source platform used for calibration. */
  source: Source;
  /** First 80 characters of the analyzed text. */
  textPreview: string;
}

// ── Errors ──────────────────────────────────────────────────────────

export class SentimentAnalysisError extends Error {
  textPreview: string;
  cause: Error | null;

  constructor(
    message: string,
    textPreview: string = "",
    cause: Error | null = null,
  ) {
    super(message);
    this.name = "SentimentAnalysisError";
    this.textPreview = textPreview;
    this.cause = cause;
  }
}

export class InvalidResponseError extends SentimentAnalysisError {
  constructor(message: string) {
    super(message);
    this.name = "InvalidResponseError";
  }
}

// ── Prompt loading ──────────────────────────────────────────────────

let cachedTemplate: string | null = null;

function loadPromptTemplate(): string {
  if (cachedTemplate) return cachedTemplate;

  // Resolve relative to this file: ../prompts/classify-prompt.md
  const currentDir = typeof __dirname !== "undefined"
    ? __dirname
    : dirname(fileURLToPath(import.meta.url));
  const promptPath = resolve(currentDir, "..", "prompts", "classify-prompt.md");

  try {
    cachedTemplate = readFileSync(promptPath, "utf-8");
    return cachedTemplate;
  } catch {
    throw new SentimentAnalysisError(
      `Classify prompt not found at ${promptPath}. ` +
        "Ensure the prompts/ directory is alongside the typescript/ directory.",
    );
  }
}

// ── Analyzer ────────────────────────────────────────────────────────

export class SentimentAnalyzer {
  private readonly config: ResolvedConfig;
  private client: Anthropic | null = null;

  constructor(config: SentimentConfig = {}) {
    this.config = {
      model: config.model ?? "claude-sonnet-4-6",
      maxTokens: config.maxTokens ?? 256,
      temperature: config.temperature ?? 0,
      apiKey: config.apiKey,
      defaultSource: config.defaultSource ?? "general",
      maxTextLength: config.maxTextLength ?? 4000,
    };
  }

  // ---- Public API ---------------------------------------------------

  /**
   * Analyze sentiment of a single text.
   *
   * @param text - The text to analyze.
   * @param source - Source platform for calibration (reddit, hackernews, news,
   *   academic, social_media, review, general). Defaults to config.defaultSource.
   * @returns SentimentResult with sentiment, confidence, and reasoning.
   * @throws SentimentAnalysisError if the API call or parsing fails.
   */
  async analyze(text: string, source?: Source): Promise<SentimentResult> {
    if (!text || !text.trim()) {
      throw new Error("Text must be non-empty.");
    }

    const resolvedSource = this.validateSource(source);
    const truncated = this.truncate(text);
    const prompt = this.buildPrompt(truncated, resolvedSource);
    const preview = text.slice(0, 80).replace(/\n/g, " ");

    let raw: string;
    try {
      raw = await this.callLLM(prompt);
    } catch (err) {
      const error = err instanceof Error ? err : new Error(String(err));
      throw new SentimentAnalysisError(
        `Sentiment analysis failed: ${error.message}`,
        preview,
        error,
      );
    }

    const parsed = this.parseResponse(raw);

    return {
      sentiment: parsed.sentiment,
      confidence: parsed.confidence,
      reasoning: parsed.reasoning,
      source: resolvedSource,
      textPreview: preview,
    };
  }

  /**
   * Analyze sentiment for multiple texts.
   *
   * @param items - Array of strings or [text, source] tuples.
   * @returns Array of SentimentResult, one per input.
   */
  async analyzeBatch(
    items: Array<string | [string, Source]>,
  ): Promise<SentimentResult[]> {
    const results: SentimentResult[] = [];
    for (const item of items) {
      if (typeof item === "string") {
        results.push(await this.analyze(item));
      } else {
        results.push(await this.analyze(item[0], item[1]));
      }
    }
    return results;
  }

  // ---- Internal -----------------------------------------------------

  private getClient(): Anthropic {
    if (!this.client) {
      const apiKey =
        this.config.apiKey ?? process.env.ANTHROPIC_API_KEY;
      if (!apiKey) {
        throw new SentimentAnalysisError(
          "No API key provided. Pass apiKey in SentimentConfig " +
            "or set the ANTHROPIC_API_KEY environment variable.",
        );
      }
      this.client = new Anthropic({ apiKey });
    }
    return this.client;
  }

  private validateSource(source?: Source): Source {
    const resolved = source ?? this.config.defaultSource;
    if (!VALID_SOURCES.has(resolved)) {
      throw new Error(
        `Invalid source '${resolved}'. Must be one of: ${[...VALID_SOURCES].sort().join(", ")}`,
      );
    }
    return resolved;
  }

  private truncate(text: string): string {
    if (text.length <= this.config.maxTextLength) return text;
    let truncated = text.slice(0, this.config.maxTextLength);
    const lastSpace = truncated.lastIndexOf(" ");
    if (lastSpace > this.config.maxTextLength * 0.8) {
      truncated = truncated.slice(0, lastSpace);
    }
    return truncated + " [truncated]";
  }

  private buildPrompt(text: string, source: Source): string {
    const template = loadPromptTemplate();
    return template.replace("{source}", source).replace("{text}", text);
  }

  private async callLLM(prompt: string): Promise<string> {
    const client = this.getClient();
    const response = await client.messages.create({
      model: this.config.model,
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature,
      messages: [{ role: "user", content: prompt }],
    });

    if (!response.content || response.content.length === 0) {
      throw new SentimentAnalysisError("Empty response from LLM.");
    }

    const block = response.content[0];
    if (block.type !== "text") {
      throw new SentimentAnalysisError(
        `Unexpected response block type: ${block.type}`,
      );
    }
    return block.text;
  }

  private parseResponse(raw: string): {
    sentiment: Sentiment;
    confidence: number;
    reasoning: string;
  } {
    // Try to extract JSON from code fences first
    let jsonStr: string | null = null;

    const fenceMatch = raw.match(/```(?:json)?\s*(\{.*?\})\s*```/s);
    if (fenceMatch) {
      jsonStr = fenceMatch[1];
    } else {
      const objectMatch = raw.match(/\{[^{}]*\}/s);
      if (objectMatch) {
        jsonStr = objectMatch[0];
      }
    }

    if (!jsonStr) {
      throw new InvalidResponseError(
        `No JSON object found in LLM response: ${raw.slice(0, 200)}`,
      );
    }

    let data: Record<string, unknown>;
    try {
      data = JSON.parse(jsonStr) as Record<string, unknown>;
    } catch {
      throw new InvalidResponseError(`Invalid JSON in LLM response: ${jsonStr.slice(0, 200)}`);
    }

    // Validate sentiment
    const sentiment = String(data.sentiment ?? "")
      .toLowerCase()
      .trim();
    if (!VALID_SENTIMENTS.has(sentiment)) {
      throw new InvalidResponseError(
        `Invalid sentiment '${sentiment}'. Must be one of: ${[...VALID_SENTIMENTS].sort().join(", ")}`,
      );
    }

    // Validate confidence
    if (data.confidence == null) {
      throw new InvalidResponseError(
        "Missing 'confidence' field in response.",
      );
    }
    let confidence = Number(data.confidence);
    if (Number.isNaN(confidence)) {
      throw new InvalidResponseError(
        `Invalid confidence value: ${String(data.confidence)}`,
      );
    }
    confidence = Math.max(0, Math.min(1, confidence));

    // Validate reasoning
    const reasoning = String(data.reasoning ?? "").trim();
    if (!reasoning) {
      throw new InvalidResponseError("Missing or empty 'reasoning' field.");
    }

    return {
      sentiment: sentiment as Sentiment,
      confidence,
      reasoning,
    };
  }
}

// ── Convenience function ────────────────────────────────────────────

/**
 * One-shot convenience function for sentiment analysis.
 *
 * @param text - The text to analyze.
 * @param source - Source platform for calibration (default: "general").
 * @param model - Claude model to use (default: "claude-sonnet-4-6").
 * @param apiKey - Anthropic API key (or set ANTHROPIC_API_KEY env var).
 * @returns SentimentResult with sentiment, confidence, and reasoning.
 */
export async function analyzeSentiment(
  text: string,
  source: Source = "general",
  model: string = "claude-sonnet-4-6",
  apiKey?: string,
): Promise<SentimentResult> {
  const analyzer = new SentimentAnalyzer({ model, apiKey });
  return analyzer.analyze(text, source);
}
