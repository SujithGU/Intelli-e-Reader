import { Component, ElementRef, HostListener, OnInit, ViewChild } from '@angular/core';
import { MockInput } from 'src/app/models/word_inp';
import { AppService } from 'src/app/services/app.service';
import { UtilityService } from 'src/app/services/utility.service';

@Component({
  selector: 'app-book-layout',
  templateUrl: './book-layout.component.html',
  styleUrls: ['./book-layout.component.scss']
})
export class BookLayoutComponent implements OnInit {

  inputData: any;
  // inputData = JSON.parse(JSON.stringify(new MockInput().input));
  newSentences: any = [];
  senWordList: { [key: string]: any } = {};
  wordDetails: any;
  showWordDetail = false;
  leftPos = 0;
  topPos: any;
  bottomPos: any;
  caretClass = 'caret-icon-top';
  @ViewChild('readerContainer') readerContainer: ElementRef;

  // loremText = `The capacity to enable perfectly leads to the ability to whiteboard without lessening our power to benchmark.Without efficient, transparent bloatware, you will lack cross-media CAE.
  //     The capacity to enable perfectly leads to the ability to whiteboard without lessening our power to benchmark.Without efficient, transparent bloatware, you will lack cross-media CAE.That is a remarkable achievement taking into account this month's financial state of things! If all of this comes off as mixed-up to you, that's because it is! If you transition globally, you may also mesh iteravely.We apply the proverb 'A rolling stone gathers no moss' not only on our feature set, but our back-end performance and non-complex use is usually considered a remarkable achievement.We think we know that it is better to engineer seamlessly.Our feature set is unmatched in the industry, but our newbie-proof administration and simple configuration.Our infinitely reconfigurable feature set is unmatched in the industry, but our back-end performance and non-complex configuration is frequently considered a remarkable achievement taking into account this month's financial state of things!If all of this may seem confusing, but it's accurate!
  // We will enlarge our ability to whiteboard without lessening our power to deliver.Have you ever needed to matrix your cutting-edge feature set? Free? Think B2C2B.
  // It may seem terrific, but it's 100%̉̉̉ realistic! What does the industry jargon 'co-branded' really mean?`
  loremText: string;
  bookTitle = 'Treasure Island';

  @HostListener('document:click', ['$event']) onClick(event: MouseEvent) {
    const isInside = event.composedPath().includes(this.readerContainer.nativeElement);
    if (!isInside) {
      this.showWordDetail = false;
    }
  }

  // @HostListener('window:scroll', [])
  // onWindowScroll() {
  //   this.showWordDetail = false;
  // }


  constructor(
    private appService: AppService,
    private utilityService: UtilityService
  ) { }

  ngOnInit(): void {
    // this.loremText = undefined;
    if (this.utilityService.isDefined(this.appService.book) && this.utilityService.isDefined(this.appService.wordTree)) {
      this.loremText = this.appService.book;
      this.inputData = this.appService.wordTree;
      if (!this.utilityService.isEmpty(this.appService.bookName)) {
        this.bookTitle = this.appService.bookName;
      }
    }
    this.processText(this.loremText);
    // console.log(this.newSentences)
  }


  processText(inputText: string) {
    let wordsList: any = []
    let newSentence = ''
    const sentences = inputText.split('.')
    for (let sentenceIndex in inputText.split('.')) {
      newSentence = ''
      const key = 'sentence_' + sentenceIndex;
      // sentences[sentenceIndex] = sentences[sentenceIndex].trim();
      const words = sentences[sentenceIndex].split(' ')
      wordsList = []
      let wordIndex = 0;
      let validWordIndex = 0
      while (wordIndex < words.length) {
        // Checks if its a valid word.
        // if (words[wordIndex].replace(',', '').match('^[a-zA-Z]+$')) {
        if (words[wordIndex] !== '\t' && words[wordIndex] !== '\n') {
          const indexKey = 'index_' + validWordIndex;
          if (this.inputData[key] && this.inputData[key][indexKey] !== undefined && words[wordIndex].replace(',', '').toLowerCase() == this.inputData[key][indexKey].word) {
            const newWord = '<mark>' + words[wordIndex] + '</mark>';
            newSentence += newWord;
          } else {
            newSentence += words[wordIndex];
          }
          validWordIndex++;
          wordsList.push(words[wordIndex]);
        } else {
          // Put spaces.
          if (words[wordIndex] == '\t') {
            newSentence += '&nbsp&nbsp&nbsp&nbsp';
          } else if (words[wordIndex] == '\n') {
            newSentence += '<br>';
          }
        }
        if (wordIndex !== words.length - 1) {
          newSentence += ' '
        }
        wordIndex++;
        // break;
      }
      this.senWordList[key] = wordsList;
      newSentence += '.';
      this.newSentences.push(newSentence);
    }

  }

  clickFunc(event: any, sentenceNo: any) {
    this.showWordDetail = false;
    // console.log(event.clientY);
    if (event.target.nodeName === 'MARK') {
      // console.log('Marked element clicked' + ' and word is ' + event.target.outerText + ' and sentence no ' + sentenceNo)
      const clickedWord = event.target.outerText;
      const senKey = 'sentence_' + sentenceNo;
      const wordIndex = this.senWordList[senKey].indexOf(clickedWord);
      this.wordDetails = this.inputData[senKey]['index_' + wordIndex];

      // Set positioning.
      this.leftPos = event.clientX - 40;
      // this.topPos = event.clientY + 15 + window.scrollY;
      if (window.innerHeight - event.clientY >= 300) {
        this.bottomPos = undefined;
        this.topPos = event.clientY + 15 + window.scrollY;
        this.caretClass = 'caret-icon-top';
      } else {
        this.bottomPos = (window.innerHeight - event.clientY) - window.scrollY + 15;
        this.topPos = undefined;
        this.caretClass = 'caret-icon-bottom';
      }
      this.showWordDetail = true;
    }
  }

}
