class Panoptes < Formula
  desc "Local repository structure and retrieval CLI for coding agents"
  homepage "https://github.com/wallentx/panoptes"
  license "MIT"

  head do
    url "https://github.com/wallentx/panoptes.git", branch: "main"
    depends_on "rust" => :build
  end

  depends_on "git"

  on_macos do
    on_arm do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.2/panoptes-1.0.2-aarch64-apple-darwin.tar.gz"
      sha256 "5613a0c5aed738b976a0e058f54293bd85448162f14f77337b9c9e7956010fc9"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.2/panoptes-1.0.2-x86_64-apple-darwin.tar.gz"
      sha256 "d740383102cceb59eb4bdd7e0207e61c58e645c72637814a8a4126862d4e729e"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.2/panoptes-1.0.2-aarch64-unknown-linux-gnu.tar.gz"
      sha256 "36fdd1b24f7302d14d5173f627604c4a70411beec6905a596732ef585714c051"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.2/panoptes-1.0.2-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "f36361593ca8ad2e318b7b6cbed07a18edc6bbc62c61b4551d7297398bc273f8"
    end
  end

  def install
    if build.head?
      ENV["PANOPTES_GIT_SHA"] = Utils.git_head
      system "cargo", "install", *std_cargo_args
      generate_completions_from_executable(bin/"panoptes", "completions")
    else
      bin.install "panoptes"
      bash_completion.install "completions/panoptes.bash" => "panoptes"
      zsh_completion.install "completions/_panoptes"
      fish_completion.install "completions/panoptes.fish"
    end
  end

  def caveats
    <<~EOS
      Configure your coding agent after installation, for example:
        panoptes init --provider cursor --provider opencode

      After upgrades, rerun panoptes init for your providers and restart
      their MCP clients so they use the newly installed executable.
    EOS
  end

  test do
    unless build.head?
      metadata = JSON.parse(shell_output("#{bin}/panoptes version --json"))
      assert_equal version.to_s, metadata.fetch("version")
    end

    (testpath/"src/example.ts").write <<~TYPESCRIPT
      export function greet(name: string) { return "hello " + name; }
      export function main() { return greet("world"); }
    TYPESCRIPT
    system "git", "init", "--quiet", testpath

    store = testpath/"panoptes.db"
    system bin/"panoptes", "--store", store, "build", testpath
    results = JSON.parse(shell_output("#{bin}/panoptes --store #{store} grep greet --path #{testpath} --json"))
    assert_equal 1, results.length
    result = results.fetch(0)
    assert_equal 2, result.fetch("total_hits")
    assert_equal 0, result.fetch("unreadable")
    system bin/"panoptes", "--store", store, "check", testpath
  end
end
