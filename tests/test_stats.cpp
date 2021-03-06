#include "gtest/gtest.h"

#include <random>
#include <vector>

#include "population_model.h"

auto beta_distribution(double alpha, double beta, std::mt19937* random_generator) -> double {
  std::gamma_distribution<> X(alpha, 1), Y(beta, 1);
  double x = X(*random_generator), y = Y(*random_generator);
  return x / (x + y);
}

TEST(PopulationModel, GeneratesSymptoms) {
  PopulationModel population_model;
  constexpr uint32_t kIterations = 1 << 16;
  for (uint32_t age_decade : {1, 5, 8}) {
    double sum = 0;
    for (uint32_t i = 0; i < kIterations; ++i) {
      sum += static_cast<uint32_t>(population_model.GenerateSymptoms(age_decade) > 0.5);
    }
    double result = sum / kIterations;
    EXPECT_NEAR(kDeathProbabilities[age_decade], result, 0.02);
  }
}

TEST(PopulationModel, CalculatesQuantiles) {
  std::random_device rd;
  std::mt19937 generator(rd());
  constexpr uint32_t kIterations = 1 << 20;

  double quantile = 1 - 5450 / kPopulationSize;  // 99.9-th percentile of population
  constexpr double kBeta = 80;
  PopulationModel population_model;
  double threshold = population_model.CalculateThreshold(kBeta, quantile);
  double sum = 0;
  for (uint32_t i = 0; i < kIterations; ++i) {
    sum += static_cast<double>(beta_distribution(1, kBeta, &generator) < threshold);
  }

  sum /= kIterations;
  EXPECT_NEAR(sum, quantile, 0.001);
}

TEST(PopulationModel, GeneratesAgeAccordingToPopulation) {
  constexpr uint32_t kIterations = 1 << 22;
  std::vector<double> occurences(kDecadesCount, 0.0);
  PopulationModel population_model;
  for (uint32_t i = 0; i < kIterations; ++i) {
    occurences[population_model.GenerateAgeDecade()] += 1;
  }
  for (auto& occurence : occurences) occurence /= kIterations;
  for (uint32_t i = 0; i < kDecadesCount; ++i) {
    EXPECT_NEAR(occurences[i], kPopulationAge[i], 0.001);
  }
}

TEST(PopulationModel, GeneratesAccordingToPoisson) {
  constexpr uint32_t kIterations = 1 << 20;
  constexpr uint32_t kSentinel = 1 << 18;
  std::vector<uint32_t> occurences(kSentinel, 0);
  constexpr uint32_t kPairSum = 22;
  PopulationModel population_model;
  for (uint32_t i = 0; i < kIterations; ++i) {
    uint32_t generated = population_model.PoissonDistribution(kPairSum / 2.0);
    if (generated < kSentinel) {
      ++occurences[generated];
    }
  }

  std::vector<double> probabilities(kSentinel, 0);
  for (uint32_t i = 0; i < kSentinel; ++i) {
    probabilities[i] = occurences[i] / static_cast<double>(kIterations);
  }

  for (uint32_t z = 0; z <= kPairSum; ++z) {
    EXPECT_NEAR(std::exp(population_model.LogDistance(z, kPairSum - z)),
                probabilities[z] * probabilities[kPairSum - z], 0.001);
  }
}
