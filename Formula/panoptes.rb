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
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.0/panoptes-1.0.0-aarch64-apple-darwin.tar.gz"
      sha256 "35237546139211480bb0a5e641c03b04d92501029d967bcc89e55f2514f7bc8d"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.0/panoptes-1.0.0-x86_64-apple-darwin.tar.gz"
      sha256 "fe3b8f3db1559d9ceca21f6db92d5d55a9a62ad52a72aeb4a88bfa961294c114"
    end
  end

  on_linux do
    on_arm do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.0/panoptes-1.0.0-aarch64-unknown-linux-gnu.tar.gz"
      sha256 "51fafd96e6df1b7b2565e37984162533247ad81eb53509617a839f2cb577faf4"
    end

    on_intel do
      url "https://github.com/wallentx/panoptes/releases/download/v1.0.0/panoptes-1.0.0-x86_64-unknown-linux-gnu.tar.gz"
      sha256 "5f7de858a690279dbb0d960d32ee7326afe3ad0a23d1bd3173b999ca4233429a"
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
