import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpHeaders } from '@angular/common/http';
import { throwError as observableThrowError, Observable, of } from 'rxjs';
import { map, catchError } from 'rxjs/operators';
import { DummyResponse } from '../models/dummy-resp';

@Injectable({
  providedIn: 'root'
})
export class AppService {

  fileDetails:any;
  endpoint = 'http://b0183874deba.ngrok.io/';
  wordTree: any;
  book: string;
  bookName: string;

  constructor(
    private http: HttpClient
  ) { 
    this.convertFile();
  }

  uploadFile(fileData: any): Observable<any> {
    const url = this.endpoint + 'retrieve';
    return this.http.post(url, fileData, this.getHTTPHeaderForAjaxCalls()).pipe(map(
      (res: any) => {
        console.log(res)
        this.wordTree = res.sentence_list;
        this.book = res.formatted_text;
        this.bookName = res.title;
        this.setFileDetails(res);
        return res;
      })
    ).pipe(catchError((err) => {
        return observableThrowError(err.message || err);
    }));
  }

  convertFile() {
    const url = this.endpoint + 'convert';
    const req = {
      'request': {
        'begin': 'true'
      }
    }
    const res = new DummyResponse().output;
    this.wordTree = res.sentence_list;
    this.book = res.formatted_text;
    this.bookName = res.title;
    return of(res);
    // return this.http.post(url, req, this.getHTTPHeaderForAjaxCalls()).pipe(map(
    //   (res: any) => {
    //     console.log(res)
    //     this.setFileDetails(res);
    //     return res;
    //   })
    // ).pipe(catchError((err) => {
    //     return observableThrowError(err.message || err);
    // }));
  }

  setFileDetails(fileObj: any) {
    this.fileDetails = fileObj;
  }

  retrieveFileDetails() {
    return this.fileDetails;
  }

  getHTTPHeaderForAjaxCalls() {
    return {
      headers: new HttpHeaders({
        'content-type': 'application/json',
        // tslint:disable-next-line:object-literal-key-quotes
        'Accept': 'application/json'
      }),
      withCredentials: false
    };
  }

}
