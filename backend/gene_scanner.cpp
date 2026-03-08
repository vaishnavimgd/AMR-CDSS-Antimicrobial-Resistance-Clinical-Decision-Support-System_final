/*
 * gene_scanner.cpp
 * ================
 * High-performance FASTA gene scanner for the AMR prediction system.
 *
 * Reads a FASTA genome file, concatenates all sequence lines into a single
 * uppercase DNA string, and searches for predefined resistance gene patterns.
 * Outputs a comma-separated binary vector (1 = found, 0 = absent) to stdout.
 *
 * Usage:
 *     gene_scanner.exe <path_to_fasta_file>
 *
 * Compile:
 *     g++ -O2 -std=c++17 gene_scanner.cpp -o gene_scanner.exe
 */

#include <algorithm>
#include <cstdlib>
#include <fstream>
#include <iostream>
#include <string>
#include <vector>

// ─── Resistance Gene Patterns ────────────────────────────────────────────────
// Placeholder gene signatures used for scanning.
// These will be replaced with real AMR gene sequences in production.

static const std::vector<std::string> GENE_PATTERNS = {
    "ATGAGTATTCAACATTTCCGTGTCGCCCTTATTCCC",   // geneA — blaTEM-1 fragment
    "ATGAAAAAGATAGAAATTTCTTCAGTATTCAAAGAA",    // geneB — mecA fragment
    "ATGCGTTATATTCGCCTGTGTATTATCTCCCTGTGA",    // geneC — vanA fragment
    "ATGGCAAAGACAGCTATGACCATGATTACGCCAAGC",    // geneD — tetA fragment
    "ATGATTGAACAAGATGGATTGCACGCAGGTTCTCCG",    // geneE — aac(6') fragment
};

// ─── FASTA Parser ────────────────────────────────────────────────────────────

/**
 * Parse a FASTA file and return the concatenated, uppercase genome sequence.
 *
 * - Skips header lines (starting with '>') and blank lines.
 * - Concatenates all sequence lines into one continuous string.
 * - Converts all characters to uppercase for case-insensitive matching.
 *
 * @param filepath  Path to the FASTA file.
 * @return          Concatenated uppercase genome string.
 */
std::string parse_fasta(const std::string& filepath) {
    std::ifstream file(filepath);
    if (!file.is_open()) {
        std::cerr << "Error: Cannot open file '" << filepath << "'." << std::endl;
        std::exit(1);
    }

    std::string genome;
    genome.reserve(1 << 20);  // Pre-allocate ~1 MB to reduce reallocations

    std::string line;
    while (std::getline(file, line)) {
        // Skip empty lines and header lines
        if (line.empty() || line[0] == '>') {
            continue;
        }

        // Remove trailing whitespace (handles \r from Windows line endings)
        while (!line.empty() && (line.back() == '\r' || line.back() == '\n' || line.back() == ' ')) {
            line.pop_back();
        }

        genome += line;
    }

    file.close();

    // Convert to uppercase for case-insensitive matching
    std::transform(genome.begin(), genome.end(), genome.begin(), ::toupper);

    return genome;
}

// ─── Gene Detection ──────────────────────────────────────────────────────────

/**
 * Scan the genome for each gene pattern and return a binary presence vector.
 *
 * Uses std::string::find for efficient substring searching.
 *
 * @param genome    The full uppercase genome sequence.
 * @param patterns  Vector of gene pattern strings to search for.
 * @return          Vector of 0s and 1s (1 = gene found, 0 = not found).
 */
std::vector<int> detect_genes(const std::string& genome,
                              const std::vector<std::string>& patterns) {
    std::vector<int> presence(patterns.size(), 0);

    for (size_t i = 0; i < patterns.size(); ++i) {
        if (genome.find(patterns[i]) != std::string::npos) {
            presence[i] = 1;
        }
    }

    return presence;
}

// ─── Output ──────────────────────────────────────────────────────────────────

/**
 * Print the gene presence vector as a comma-separated string to stdout.
 *
 * @param presence  Binary vector of gene detection results.
 */
void print_vector(const std::vector<int>& presence) {
    for (size_t i = 0; i < presence.size(); ++i) {
        if (i > 0) {
            std::cout << ",";
        }
        std::cout << presence[i];
    }
    std::cout << std::endl;
}

// ─── Main ────────────────────────────────────────────────────────────────────

int main(int argc, char* argv[]) {
    // Validate command-line arguments
    if (argc != 2) {
        std::cerr << "Usage: gene_scanner <fasta_file>" << std::endl;
        return 1;
    }

    const std::string filepath = argv[1];

    // Parse the FASTA file into a single genome string
    std::string genome = parse_fasta(filepath);

    if (genome.empty()) {
        std::cerr << "Error: No sequence data found in '" << filepath << "'." << std::endl;
        return 1;
    }

    // Detect gene patterns
    std::vector<int> presence = detect_genes(genome, GENE_PATTERNS);

    // Output the result
    print_vector(presence);

    return 0;
}
