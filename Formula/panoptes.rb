class Panoptes < Formula
  desc "Local repository structure and retrieval CLI for coding agents"
  homepage "https://github.com/wallentx/panoptes"
  url "https://github.com/wallentx/panoptes/archive/1c0052b5d12a624a53c6d756cff021166bb7833d.tar.gz"
  version "0.1.0"
  sha256 "a112171d4c16c66e229e068ccd024eaf21204656158c07800024dbfd50f2b762"
  license "MIT"
  head "https://github.com/wallentx/panoptes.git", branch: "main"

  depends_on "rust" => :build
  depends_on "git"

  def install
    ENV["PANOPTES_GIT_SHA"] = build.head? ? Utils.git_head : "1c0052b5d12a624a53c6d756cff021166bb7833d"
    system "cargo", "install", *std_cargo_args
    generate_completions_from_executable(bin/"panoptes", "completions")
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
